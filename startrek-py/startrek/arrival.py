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
from typing import Optional, Any, Set, Dict, MutableMapping

from .port import ShipStatus
from .port import Arrival


# noinspection PyAbstractClass
class ArrivalShip(Arrival, ABC):

    # Arrival task will be expired after 5 minutes
    # if still not completed
    EXPIRES = 300  # seconds

    def __init__(self, now: float = 0):
        super().__init__()
        # last received time (timestamp in seconds)
        if now <= 0:
            now = time.time()
        self.__expired = now + self.EXPIRES

    # Override
    def touch(self, now: float):
        # update expired time
        self.__expired = now + self.EXPIRES

    # Override
    def get_status(self, now: float) -> ShipStatus:
        if now > self.__expired:
            return ShipStatus.EXPIRED
        else:
            return ShipStatus.ASSEMBLING


class ArrivalHall:
    """ Memory cache for Arrivals """

    def __init__(self):
        super().__init__()
        self.__arrivals: Set[Arrival] = set()
        self.__map: MutableMapping[Any, Arrival] = weakref.WeakValueDictionary()  # sn => Arrival
        self.__finished_times: Dict[Any, float] = {}                              # sn => timestamp

    def assemble_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """
        Check received ship for completed package

        :param ship: income ship carrying data package/fragment
        :return a ship carrying completed data package
        """
        # 1. check ship ID (SN)
        sn = ship.sn
        if sn is None:
            # separated package ship must have SN for assembling
            # we consider it to be a ship carrying a whole package here
            return ship
        # 2. check cached ship
        cached = self.__map.get(sn)
        if cached is None:
            # check whether the task as already finished
            timestamp = self.__finished_times.get(sn, 0)
            if timestamp > 0:
                # task already finished
                return None
            # 3. new arrival, try assembling to check whether a fragment
            completed = ship.assemble(ship=ship)
            if completed is None:
                # it's a fragment, waiting for more fragments
                self.__arrivals.add(ship)
                self.__map[sn] = ship
                # ship.touch(now=time.time())
            # else, it's a completed package
        else:
            # 3. cached ship found, try assembling (insert as fragment)
            #    to check whether all fragments received
            completed = cached.assemble(ship=ship)
            if completed is None:
                # it's not completed yet, update expired time
                # and wait for more fragments.
                cached.touch(now=time.time())
            else:
                # all fragments received, remove cached ship
                self.__arrivals.discard(cached)
                self.__map.pop(sn, None)
                # mark finished time
                self.__finished_times[sn] = time.time()
        return completed

    def purge(self, now: float = 0) -> int:
        """ Clear all expired tasks """
        if now <= 0:
            now = time.time()
        count = 0
        # 1. seeking expired tasks
        arrivals = set(self.__arrivals)
        for ship in arrivals:
            if ship.get_status(now=now) == ShipStatus.EXPIRED:
                # task expired
                self.__arrivals.discard(ship)
                # remove mapping with SN
                sn = ship.sn
                if sn is not None:
                    self.__map.pop(sn, None)
                    # TODO: callback?
                count += 1
        # 2. seeking neglected finished times
        ago = now - 3600
        keys = set(self.__finished_times.keys())
        for sn in keys:
            when = self.__finished_times.get(sn)
            if when is None or when < ago:
                # long time ago
                self.__finished_times.pop(sn, None)
        return count
