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

    def __init__(self, pack: bytes, now: float = 0):
        super().__init__(now=now)
        self.__completed = pack

    @property
    def package(self) -> bytes:
        return self.__completed

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

    def __init__(self, pack: bytes, priority: int = 0):
        super().__init__(priority=priority, max_tries=1)
        self.__completed = pack
        self.__fragments = [pack]

    @property
    def package(self) -> bytes:
        return self.__completed

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

    @property  # Override
    def is_important(self) -> bool:
        # plain departure no needs response
        return False


class PlainDocker(StarDocker):

    # noinspection PyMethodMayBeStatic
    def _create_arrival(self, pack: bytes) -> Arrival:
        return PlainArrival(pack=pack)

    # noinspection PyMethodMayBeStatic
    def _create_departure(self, pack: bytes, priority: int):
        return PlainDeparture(pack=pack, priority=priority)

    # Override
    def _get_arrivals(self, data: bytes) -> List[Arrival]:
        if data is None or len(data) == 0:
            return []
        else:
            return [self._create_arrival(pack=data)]

    # Override
    async def _check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        if len(data) == 4:
            if data == PING:
                # PING -> PONG
                await self.send(payload=PONG, priority=DeparturePriority.SLOWER)
                return None
            if data == PONG or data == NOOP:
                # ignore
                return None
        return ship

    #
    #   Sending
    #

    async def send(self, payload: bytes, priority: int) -> bool:
        """ sending payload with priority """
        ship = self._create_departure(pack=payload, priority=priority)
        return await self.send_ship(ship=ship)

    # Override
    async def send_data(self, payload: Union[bytes, bytearray]) -> bool:
        return await self.send(payload=payload, priority=DeparturePriority.NORMAL)

    # Override
    async def heartbeat(self):
        await self.send(payload=PING, priority=DeparturePriority.SLOWER)


PING = b'PING'
PONG = b'PONG'
NOOP = b'NOOP'
OK = b'OK'
