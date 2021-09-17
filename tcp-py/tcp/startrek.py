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

import weakref
from typing import List, Optional

from startrek import Connection
from startrek import Arrival, ArrivalShip, Departure, DepartureShip, DeparturePriority
from startrek import ShipDelegate, GateDelegate
from startrek import StarDocker, StarGate


class PlainArrival(ArrivalShip):

    def __init__(self, data: bytes):
        super().__init__()
        self.__data = data

    @property
    def package(self) -> bytes:
        return self.__data

    @property  # Override
    def sn(self):
        # plain ship has no SN
        return None

    # Override
    def assemble(self, ship):
        assert self is ship, 'plain arrival error: %s, %s' % (ship, self)
        # plain arrival needs no assembling
        return ship


class PlainDeparture(DepartureShip):

    def __init__(self, data: bytes, priority: int = 0, delegate: Optional[ShipDelegate] = None):
        super().__init__(priority=priority, delegate=delegate)
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

    def __init__(self, remote: tuple, local: Optional[tuple], gate: StarGate):
        super().__init__(remote=remote, local=local)
        self.__gate = weakref.ref(gate)

    @property  # private
    def gate(self) -> StarGate:
        return self.__gate()

    @property  # Override
    def connection(self) -> Optional[Connection]:
        gate = self.gate
        if gate is not None:
            return gate.get_connection(remote=self.remote_address, local=self.local_address)

    @property  # Override
    def delegate(self) -> GateDelegate:
        gate = self.gate
        if gate is not None:
            return gate.delegate

    # Override
    def get_arrival(self, data: bytes) -> Optional[Arrival]:
        if data is not None and len(data) > 0:
            return PlainArrival(data=data)

    # Override
    def check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        if len(data) == 4:
            if data == PING:
                # PING -> PONG
                outgo = self.pack(payload=PONG, priority=DeparturePriority.SLOWER)
                self.append_departure(ship=outgo)
                return None
            if data == PONG or data == NOOP:
                # ignore
                return None
        return ship

    # Override
    def pack(self, payload: bytes, priority: int = 0, delegate: Optional[ShipDelegate] = None) -> Departure:
        return PlainDeparture(data=payload, priority=priority)

    # Override
    def heartbeat(self):
        outgo = self.pack(payload=PING, priority=DeparturePriority.SLOWER)
        self.append_departure(ship=outgo)

    def send_ship(self, ship: Departure):
        self.append_departure(ship=ship)

    def send_data(self, payload: bytes, priority: int = 0, delegate: Optional[ShipDelegate] = None):
        ship = self.pack(payload=payload, priority=priority, delegate=delegate)
        self.append_departure(ship=ship)


PING = b'PING'
PONG = b'PONG'
NOOP = b'NOOP'
