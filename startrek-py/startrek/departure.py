# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import time
import weakref
from abc import ABC
from typing import List, Dict, Set, Any, Optional

from .port import Arrival, Departure, ShipDelegate


class DepartureShip(Departure, ABC):

    # Departure task will be expired after 2 minutes if no response received
    EXPIRES = 120  # seconds

    # Departure task will be retried 2 times if timeout
    MAX_RETRIES = 2

    def __init__(self, priority: int = 0, delegate: Optional[ShipDelegate] = None):
        super().__init__()
        # ship priority
        self.__priority = priority
        # specific delegate for this ship
        if delegate is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(delegate)
        # last tried time (timestamp in seconds)
        self.__last_time = 0
        # totally 3 times to be sent at the most
        self.__retries = -1

    @property
    def delegate(self) -> Optional[ShipDelegate]:
        ref = self.__delegate
        if ref is not None:
            return ref()

    @property
    def priority(self) -> int:
        return self.__priority

    @property
    def retries(self) -> int:
        return self.__retries

    # Override
    def is_timeout(self, now: int) -> bool:
        expired = self.__last_time + self.EXPIRES
        return self.__retries < self.MAX_RETRIES and expired < now

    # Override
    def is_failed(self, now: int) -> bool:
        expired = self.__last_time + self.EXPIRES * (self.MAX_RETRIES - self.__retries + 2)
        return 0 < self.__last_time and expired < now

    # Override
    def update(self, now: int) -> bool:
        if self.__retries < self.MAX_RETRIES:
            # update retried time
            self.__last_time = now
            # increase counter
            self.__retries += 1
            return True
        # else, retried too many times


class DepartureHall:
    """ Memory cache for Departures """

    def __init__(self):
        super().__init__()
        self.__priorities: List[int] = []
        self.__fleets: Dict[int, List[Departure]] = {}  # priority => List[DepartureShip]
        self.__map = weakref.WeakValueDictionary()  # sn => Departure
        self.__finished_times: Dict[Any, int] = {}  # sn => timestamp

    def append_departure(self, ship: Departure) -> bool:
        """
        Append outgoing ship to a fleet with priority

        :param ship: departure task carrying data package/fragment
        :return False on duplicated
        """
        priority = ship.priority
        # 1. choose an array with priority
        fleet = self.__fleets.get(priority)
        if fleet is None:
            # 1.1. create new array for this priority
            fleet = []
            self.__fleets[priority] = fleet
            # 1.2. insert the priority in a sorted list
            self.__insert(priority=priority)
        elif ship in fleet:
            # 1.3. check duplicated
            return False
        # 2. append to the tail
        fleet.append(ship)
        # 3. build mapping if SN exists
        sn = ship.sn
        if sn is not None:
            self.__map[sn] = ship
        return True

    def __insert(self, priority: int) -> bool:
        index = 0
        for value in self.__priorities:
            if value == priority:
                # duplicated
                return False
            elif value > priority:
                # got it
                break
            else:
                # current value is smaller than the new value,
                # keep going
                index += 1
        # insert new value before the bigger one
        self.__priorities.insert(index, priority)
        return True

    def check_response(self, ship: Arrival) -> Optional[Departure]:
        """
        Check response from income ship

        :param ship: incoming ship with SN
        :return finished task
        """
        sn = ship.sn
        assert sn is not None, 'SN not found: %s' % ship
        # check whether this task has already finished
        timestamp = self.__finished_times.get(sn)
        if timestamp is not None and timestamp > 0:
            return None
        # check departure task
        outgo = self.__map.get(sn, None)
        if outgo is None:
            return None
        # assert isinstance(outgo, Departure), 'outgo task error: %s' % outgo
        if outgo.check_response(ship=ship):
            # all fragments sent, departure task finished
            # remove it and clear mapping when SN exists
            self.__remove(ship=outgo, sn=sn)
            # mark finished time
            self.__finished_times[sn] = int(time.time())
            return outgo

    def __remove(self, ship: Departure, sn):
        priority = ship.priority
        fleet = self.__fleets.get(priority)
        if fleet is not None and ship in fleet:
            fleet.remove(ship)
            # remove array when empty
            if len(fleet) == 0:
                self.__fleets.pop(priority, None)
        # remove mapping by SN
        self.__map.pop(sn, None)

    def next_departure(self, now: int) -> Optional[Departure]:
        """
        Get next new/timeout task

        :param now: current time
        :return departure task
        """
        # task.retries == 0
        task = self.__next_new_departure(now=now)
        if task is None:
            # task.retries < MAX_RETRIES and timeout
            task = self.__next_timeout_departure(now=now)
        return task

    def __next_new_departure(self, now: int) -> Optional[Departure]:
        for priority in self.__priorities:
            # 1. get tasks with priority
            fleet = self.__fleets.get(priority)
            if fleet is None:
                continue
            # 2. seeking new task in this priority
            for ship in fleet:
                if ship.retries == -1 and ship.update(now=now):
                    # first time to try, update and remove from the queue
                    fleet.remove(ship)
                    sn = ship.sn
                    if sn is not None:
                        self.__map.pop(sn, None)
                    return ship

    def __next_timeout_departure(self, now: int) -> Optional[Departure]:
        failed_tasks: Set[Departure] = set()
        for priority in self.__priorities:
            # 1. get tasks with priority
            fleet = self.__fleets.get(priority)
            if fleet is None:
                continue
            # 2. seeking timeout task in this priority
            for ship in fleet:
                if ship.is_timeout(now=now) and ship.update(now=now):
                    # first time to try, update and remove from the queue
                    fleet.remove(ship)
                    sn = ship.sn
                    if sn is not None:
                        self.__map.pop(sn, None)
                    self.__clear(fleet=fleet, failed_tasks=failed_tasks, priority=priority)
                    return ship
                elif ship.is_failed(now=now):
                    # task expired, remove this ship
                    failed_tasks.add(ship)
            # 2. clear failed tasks in this fleet and go on
            self.__clear(fleet=fleet, failed_tasks=failed_tasks, priority=priority)
            failed_tasks.clear()

    def __clear(self, fleet: List[Departure], failed_tasks: Set[Departure], priority: int):
        # remove expired tasks
        for ship in failed_tasks:
            fleet.remove(ship)
            # remove mapping when SN exists
            sn = ship.sn
            if sn is not None:
                self.__map.pop(sn, None)
            # TODO: callback?
        # remove array when empty
        if len(fleet) == 0:
            self.__fleets.pop(priority, None)

    def purge(self):
        """ Clear all expired tasks """
        failed_tasks: Set[Departure] = set()
        now = int(time.time())
        for priority in self.__priorities:
            # 0. get tasks with priority
            fleet = self.__fleets.get(priority)
            if fleet is None:
                continue
            # 1. seeking expired task in this priority
            for ship in fleet:
                if ship.is_failed(now=now):
                    # task expired
                    failed_tasks.add(ship)
            # 2. clear expired tasks
            self.__clear(fleet=fleet, failed_tasks=failed_tasks, priority=priority)
            failed_tasks.clear()
