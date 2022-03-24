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
from typing import Optional, Set, Dict, Any

from .port import Arrival


class ArrivalShip(Arrival, ABC):

    # Arrival task will be expired after 10 minutes if still not completed
    EXPIRES = 600  # seconds

    def __init__(self, now: float = 0):
        super().__init__()
        # last received time (timestamp in seconds)
        if now <= 0:
            now = time.time()
        self.__expired = now + self.EXPIRES

    #
    #   task states
    #

    # Override
    def is_timeout(self, now: float) -> bool:
        return now > self.__expired

    # Override
    def touch(self, now: float):
        self.__expired = now + self.EXPIRES


class ArrivalHall:
    """ Memory cache for Arrivals """

    def __init__(self):
        super().__init__()
        self.__arrivals: Set[Arrival] = set()
        self.__map = weakref.WeakValueDictionary()  # sn => Arrival
        self.__finished_times: Dict[Any, float] = {}  # sn => timestamp

    def assemble_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """
        Check received ship for completed package

        :param ship: income ship carrying data package/fragment
        :return a ship carrying completed data package
        """
        # check ship ID (SN)
        sn = ship.sn
        if sn is None:
            # separated package ship must have SN for assembling
            # we consider it to be a ship carrying a whole package here
            return ship
        # check whether the task as already finished
        timestamp = self.__finished_times.get(sn)
        if timestamp is not None and timestamp > 0:
            # task already finished
            return None
        task: Arrival = self.__map.get(sn)
        if task is None:
            # new arrival, try assembling to check whether a fragment
            task = ship.assemble(ship=ship)
            if task is None:
                # it's a fragment, waiting for more fragments
                self.__arrivals.add(ship)
                self.__map[sn] = ship
                return None
            else:
                # it's a completed package
                return task
        # insert as fragment
        completed = task.assemble(ship=ship)
        if completed is None:
            # not completed yet, update expired time
            # and wait for more fragments.
            task.touch(now=time.time())
            return None
        # all fragments received, remove this task
        self.__arrivals.discard(task)
        self.__map.pop(sn, None)
        # mark finished time
        self.__finished_times[sn] = time.time()
        return completed

    def purge(self):
        """ Clear all expired tasks """
        failed_tasks: Set[Arrival] = set()
        now = time.time()
        # 1. seeking expired tasks
        arrivals = set(self.__arrivals)
        for ship in arrivals:
            if ship.is_timeout(now=now):
                # task expired
                failed_tasks.add(ship)
        # 2. clear expired tasks
        for ship in failed_tasks:
            self.__arrivals.discard(ship)
            # remove mapping with SN
            self.__map.pop(ship.sn, None)
            # TODO: callback?
        # 3. seeking neglected finished times
        neglected_times = set()
        ago = now - 3600
        keys = set(self.__finished_times.keys())
        for sn in keys:
            when = self.__finished_times.get(sn)
            if when is None or when < ago:
                # long time ago
                neglected_times.add(sn)
        # 4. clear neglected times
        for sn in neglected_times:
            self.__finished_times.pop(sn, None)
            self.__map.pop(sn, None)
