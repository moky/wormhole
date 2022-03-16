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

from typing import List, Optional, Union

from startrek import Arrival, ArrivalShip
from startrek import DepartureShip, DeparturePriority
from startrek import StarDocker


class PlainArrival(ArrivalShip):

    def __init__(self, data: bytes, now: float = 0):
        super().__init__(now=now)
        self.__data = data

    @property
    def package(self) -> bytes:
        return self.__data

    @property  # Override
    def sn(self):
        # plain ship has no SN
        return None

    # Override
    def assemble(self, ship: Arrival):
        assert self is ship, 'plain arrival error: %s, %s' % (ship, self)
        # plain arrival needs no assembling
        return self


class PlainDeparture(DepartureShip):

    def __init__(self, data: bytes, priority: int = 0, now: float = 0):
        super().__init__(priority=priority, now=now)
        self.__data = data
        self.__fragments = [data]

    @property
    def package(self) -> bytes:
        return self.__data

    @property  # Override
    def sn(self):
        # plain ship has no SN
        return None

    @property  # Override
    def fragments(self) -> List[bytes]:
        return self.__fragments

    # Override
    def check_response(self, ship: Arrival) -> bool:
        # plain departure needs no response
        return False


class PlainDocker(StarDocker):

    # noinspection PyMethodMayBeStatic
    def _create_arrival(self, data: bytes) -> Arrival:
        return PlainArrival(data=data)

    # Override
    def _get_arrival(self, data: bytes) -> Optional[Arrival]:
        if data is not None and len(data) > 0:
            return self._create_arrival(data=data)

    # Override
    def _check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        if len(data) == 4:
            if data == PING:
                # PING -> PONG
                self.send(payload=PONG, priority=DeparturePriority.SLOWER)
                return None
            if data == PONG or data == NOOP:
                # ignore
                return None
        return ship

    #
    #   Sending
    #

    def send(self, payload: bytes, priority: int) -> bool:
        """ sending payload with priority """
        ship = PlainDeparture(data=payload, priority=priority)
        return self.send_ship(ship=ship)

    # Override
    def send_data(self, payload: Union[bytes, bytearray]) -> bool:
        return self.send(payload=payload, priority=DeparturePriority.NORMAL)

    # Override
    def heartbeat(self):
        self.send(payload=PING, priority=DeparturePriority.SLOWER)


PING = b'PING'
PONG = b'PONG'
NOOP = b'NOOP'
OK = b'OK'
