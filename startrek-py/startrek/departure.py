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
from typing import Optional, Any, List, Dict, MutableMapping

from .port import ShipStatus
from .port import Arrival, Departure


# noinspection PyAbstractClass
class DepartureShip(Departure, ABC):

    # Departure task will be expired after 2 minutes
    # if no response received.
    EXPIRES = 120  # seconds

    # Important departure task will be retried 2 times
    # if response timeout.
    RETRIES = 2

    def __init__(self, priority: int = 0, max_tries: int = None):  # max_tries = 1 + RETRIES
        super().__init__()
        # task priority, smaller is faster
        self.__priority = priority
        # expired time (timestamp in seconds)
        self.__expired = 0
        # how many times to try sending
        self.__tries = (1 + self.RETRIES) if max_tries is None else max_tries

    @property
    def priority(self) -> int:
        return self.__priority

    # Override
    def touch(self, now: float):
        assert self.__tries > 0, 'touch error, tries=%d' % self.__tries
        # decrease counter
        self.__tries -= 1
        # update retried time
        self.__expired = now + self.EXPIRES

    # Override
    def get_status(self, now: float) -> ShipStatus:
        fragments = self.fragments
        if fragments is None or len(fragments) == 0:
            return ShipStatus.DONE
        elif self.__expired == 0:
            return ShipStatus.NEW
        # elif not self.is_important:
        #     return ShipStatus.DONE
        elif now < self.__expired:
            return ShipStatus.WAITING
        elif self.__tries > 0:
            return ShipStatus.TIMEOUT
        else:
            return ShipStatus.FAILED


class DepartureHall:
    """ Memory cache for Departures """

    def __init__(self):
        super().__init__()
        # all departure ships
        self.__all_departures = weakref.WeakSet()
        # new ships waiting to send out
        self.__new_departures: List[Departure] = []
        # ships waiting for responses
        self.__fleets: Dict[int, List[Departure]] = {}  # priority => List[Departure]
        self.__priorities: List[int] = []
        # index
        self.__map: MutableMapping[Any, Departure] = weakref.WeakValueDictionary()  # SN => ship
        self.__finished_times: Dict[Any, float] = {}                                # SN => timestamp
        self.__departure_level: Dict[Any, int] = {}                                 # SN => priority

    def add_departure(self, ship: Departure) -> bool:
        """
        Add outgoing ship to the waiting queue

        :param ship: departure task
        :return: false on duplicated
        """
        # 1. check duplicated
        if ship in self.__all_departures:
            return False
        else:
            self.__all_departures.add(ship)
        # 2. insert to the sorted queue
        priority = ship.priority
        index = len(self.__new_departures)
        while index > 0:
            index -= 1
            if self.__new_departures[index].priority <= priority:
                # take the place before first ship
                # which priority is greater than this one.
                index += 1  # insert after
                break
        self.__new_departures.insert(index, ship)
        return True

    def check_response(self, ship: Arrival) -> Optional[Departure]:
        """
        Check response from income ship

        :param ship: incoming ship with SN
        :return finished task
        """
        sn = ship.sn
        assert sn is not None, 'Ship SN not found: %s' % ship
        # check whether this task has already finished
        timestamp = self.__finished_times.get(sn)
        if timestamp is not None and timestamp > 0:
            # task already finished
            return None
        # check departure task
        outgo = self.__map.get(sn, None)
        if outgo is not None and outgo.check_response(ship=ship):
            # all fragments sent, departure task finished
            # remove it and clear mapping when SN exists
            self.__remove_ship(ship=outgo, sn=sn)
            # mark finished time
            self.__finished_times[sn] = time.time()
            return outgo

    def __remove_ship(self, ship: Departure, sn):
        priority = self.__departure_level.get(sn)
        fleet = self.__fleets.get(priority)
        if fleet is not None and ship in fleet:
            fleet.remove(ship)
            # remove array when empty
            if len(fleet) == 0:
                self.__fleets.pop(priority, None)
        # remove mapping by SN
        self.__map.pop(sn, None)
        self.__departure_level.pop(sn, None)
        self.__all_departures.discard(ship)

    def next_departure(self, now: float) -> Optional[Departure]:
        """
        Get next new/timeout task

        :param now: current time
        :return departure task
        """
        # task.__expired == 0
        task = self.__next_new_departure(now=now)
        if task is None:
            # task.__expired < now
            task = self.__next_timeout_departure(now=now)
        return task

    def __next_new_departure(self, now: float) -> Optional[Departure]:
        if len(self.__new_departures) > 0:
            # get first ship
            outgo = self.__new_departures.pop(0)
            sn = outgo.sn
            if outgo.is_important and sn is not None:
                # this task needs response
                # choose an array with priority
                priority = outgo.priority
                self.__insert_ship(ship=outgo, priority=priority, sn=sn)
                # build index for it
                self.__map[sn] = outgo
            else:
                # disposable ship needs no response,
                # remove it immediately
                self.__all_departures.discard(outgo)
            outgo.touch(now=now)
            return outgo

    def __insert_ship(self, ship: Departure, priority: int, sn):
        fleet = self.__fleets.get(priority)
        if fleet is None:
            # create new array for this priority
            fleet = []
            self.__fleets[priority] = fleet
            # insert the priority in a sorted list
            self.__insert_priority(priority=priority)
        # append to the tail, and build index for it
        fleet.append(ship)
        self.__departure_level[sn] = priority

    def __insert_priority(self, priority: int) -> bool:
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

    def __next_timeout_departure(self, now: float) -> Optional[Departure]:
        # no need to copy the list being changed because it will return immediately
        priorities = self.__priorities  # list(self.__priorities)
        for prior in priorities:
            # 1. get tasks with priority
            fleet = self.__fleets.get(prior)
            if fleet is None:
                continue
            # 2. seeking timeout task in this priority
            departures = fleet  # list(fleet)
            for ship in departures:
                sn = ship.sn
                status = ship.get_status(now=now)
                if status == ShipStatus.TIMEOUT:
                    # response timeout, needs retry now.
                    # move to next priority
                    fleet.remove(ship)
                    self.__insert_ship(ship=ship, priority=(prior + 1), sn=sn)
                    # update expired time;
                    ship.touch(now=now)
                    return ship
                elif status == ShipStatus.FAILED:
                    # try too many times and still missing response,
                    # task failed, remove this ship.
                    fleet.remove(ship)
                    # remove mapping by SN
                    self.__map.pop(sn, None)
                    self.__departure_level.pop(sn, None)
                    self.__all_departures.discard(ship)
                    return ship

    def purge(self, now: float = 0) -> int:
        """ Clear all expired tasks """
        if now <= 0:
            now = time.time()
        count = 0
        # 1. seeking finished tasks
        priorities = list(self.__priorities)
        for prior in priorities:
            fleet = self.__fleets.get(prior)
            if fleet is None:
                # this priority is empty
                self.__priorities.remove(prior)
                continue
            departures = list(fleet)
            for ship in departures:
                if ship.get_status(now=now) == ShipStatus.DONE:
                    # task done, remove if from memory cache
                    sn = ship.sn
                    assert sn is not None, 'Ship SN should not be empty here'
                    fleet.remove(ship)
                    # remove mapping by SN
                    self.__map.pop(sn, None)
                    self.__departure_level.pop(sn, None)
                    self.__all_departures.discard(ship)
                    # mark finished time
                    self.__finished_times[sn] = now
                    count += 1
            # remove array when empty
            if len(fleet) == 0:
                self.__fleets.pop(prior, None)
                self.__priorities.remove(prior)
        # 2. seeking neglected finished times
        ago = now - 3600
        keys = set(self.__finished_times.keys())
        for sn in keys:
            when = self.__finished_times.get(sn)
            if when is None or when < ago:
                # long time ago
                self.__finished_times.pop(sn, None)
        return count
