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

from typing import List, Optional

from startrek import Arrival, ArrivalShip
from startrek import Departure, DepartureShip, DeparturePriority
from startrek import StarPorter


class PlainArrival(ArrivalShip):

    def __init__(self, payload: bytes, now: float = 0):
        super().__init__(now=now)
        self.__completed = payload

    def __str__(self) -> str:
        cname = self.__class__.__name__
        size = len(self.__completed)
        return '<%s: size=%d />' % (cname, size)

    def __repr__(self) -> str:
        cname = self.__class__.__name__
        size = len(self.__completed)
        return '<%s: size=%d />' % (cname, size)

    @property
    def payload(self) -> bytes:
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

    def __init__(self, payload: bytes, priority: int = 0, needs_respond: bool = False):
        super().__init__(priority=priority, max_tries=1)
        self.__completed = payload
        self.__fragments = [payload]
        self.__important = needs_respond

    def __str__(self) -> str:
        cname = self.__class__.__name__
        size = len(self.__completed)
        return '<%s: size=%d />' % (cname, size)

    def __repr__(self) -> str:
        cname = self.__class__.__name__
        size = len(self.__completed)
        return '<%s: size=%d />' % (cname, size)

    @property
    def payload(self) -> bytes:
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
        return self.__important


class PlainPorter(StarPorter):

    # noinspection PyMethodMayBeStatic
    def _create_arrival(self, payload: bytes) -> Arrival:
        return PlainArrival(payload=payload)

    # noinspection PyMethodMayBeStatic
    def _create_departure(self, payload: bytes, priority: int, needs_respond: bool) -> Departure:
        return PlainDeparture(payload=payload, priority=priority, needs_respond=needs_respond)

    # Override
    def _get_arrivals(self, data: bytes) -> List[Arrival]:
        if data is None or len(data) == 0:
            return []
        else:
            return [self._create_arrival(payload=data)]

    # Override
    async def _check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.payload
        if len(data) == 4:
            if data == PING:
                # PING -> PONG
                await self.respond(payload=PONG)
                return None
            if data == PONG or data == NOOP:
                # ignore
                return None
        return ship

    #
    #   Sending
    #

    async def respond(self, payload: bytes) -> bool:
        """ sending response """
        priority = DeparturePriority.SLOWER.value
        ship = self._create_departure(payload=payload, priority=priority, needs_respond=False)
        return await self.send_ship(ship=ship)

    async def send(self, payload: bytes, priority: int) -> bool:
        """ sending payload with priority """
        ship = self._create_departure(payload=payload, priority=priority, needs_respond=True)
        return await self.send_ship(ship=ship)

    # Override
    async def send_data(self, payload: bytes) -> bool:
        priority = DeparturePriority.NORMAL.value
        return await self.send(payload=payload, priority=priority)

    # Override
    async def heartbeat(self):
        priority = DeparturePriority.SLOWER.value
        ship = self._create_departure(payload=PING, priority=priority, needs_respond=False)
        await self.send_ship(ship=ship)


PING = b'PING'
PONG = b'PONG'
NOOP = b'NOOP'
OK = b'OK'
