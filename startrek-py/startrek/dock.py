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

import threading
from typing import Optional

from .arrival import Arrival, ArrivalHall
from .departure import Departure, DepartureHall


"""
    Star Dock
    ~~~~~~~~~

    Parking Star Ships
"""


class Dock:

    def __init__(self):
        super().__init__()
        # memory caches
        self.__arrival_hall = self._create_arrival_hall()
        self.__departure_hall = self._create_departure_hall()

    # noinspection PyMethodMayBeStatic
    def _create_arrival_hall(self) -> ArrivalHall:
        """ Override for user-customized hall """
        return ArrivalHall()

    # noinspection PyMethodMayBeStatic
    def _create_departure_hall(self) -> DepartureHall:
        """ Override for user-customized hall """
        return DepartureHall()

    def assemble_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """
        Check income ship for completed package

        :param ship: received ship carrying data package/fragment
        :return a ship carrying completed data package
        """
        # check fragment from income ship,
        # return a ship with completed package if all fragments received
        return self.__arrival_hall.assemble_arrival(ship=ship)

    def add_departure(self, ship: Departure) -> bool:
        """
        Add outgoing ship to the waiting queue

        :param ship: departure task
        :return False on duplicated
        """
        return self.__departure_hall.add_departure(ship=ship)

    def check_response(self, ship: Arrival) -> Optional[Departure]:
        """
        Check response from the income ship

        :param ship: income ship with SN
        :return finished departure task
        """
        # check departure tasks with SN
        # remove package/fragment if matched (check page index for fragments too)
        return self.__departure_hall.check_response(ship=ship)

    def next_departure(self, now: float) -> Optional[Departure]:
        """
        Get next new/timeout task

        :param now: current timestamp
        :return departure task
        """
        # this will be remove from the queue,
        # if needs retry, the caller should append it back
        return self.__departure_hall.next_departure(now=now)

    def purge(self, now: float = 0):
        """ Clear all expired tasks """
        count = 0
        count += self.__arrival_hall.purge(now=now)
        count += self.__departure_hall.purge(now=now)
        return count


class LockedDock(Dock):

    def __init__(self):
        super().__init__()
        self.__lock = threading.Lock()
        # purge
        self.__next_purge_time = 0

    # Override
    def assemble_arrival(self, ship: Arrival) -> Optional[Arrival]:
        with self.__lock:
            return super().assemble_arrival(ship=ship)

    # Override
    def add_departure(self, ship: Departure) -> bool:
        with self.__lock:
            return super().add_departure(ship=ship)

    # Override
    def check_response(self, ship: Arrival) -> Optional[Departure]:
        with self.__lock:
            return super().check_response(ship=ship)

    # Override
    def next_departure(self, now: float) -> Optional[Departure]:
        with self.__lock:
            return super().next_departure(now=now)

    # Override
    def purge(self, now: float = 0) -> int:
        if now < self.__next_purge_time:
            return -1
        else:
            # next purge after half a minute
            self.__next_purge_time = now + 30
        with self.__lock:
            return super().purge(now=now)
