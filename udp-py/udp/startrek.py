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
from startrek import ShipDelegate
from startrek import StarDocker, StarGate

from .ba import Data
from .mtp import DataType, TransactionID, Package, Packer


class PackageArrival(ArrivalShip):

    def __init__(self, pack: Package):
        super().__init__()
        head = pack.head
        self.__sn = head.sn
        if head.data_type.is_fragment:
            self.__packer = Packer(sn=head.sn, pages=head.pages)
            self.__completed = self.__packer.insert(fragment=pack)
        else:
            self.__packer = None
            self.__completed = pack

    @property
    def package(self) -> Optional[Package]:
        return self.__completed

    @property
    def fragments(self) -> Optional[List[Package]]:
        packer = self.__packer
        if packer is not None:
            assert isinstance(packer, Packer), 'packer error: %s' % packer
            return packer.fragments

    @property  # Override
    def sn(self) -> TransactionID:
        return self.__sn

    # Override
    def assemble(self, ship):  # -> Optional[PackageArrival]:
        if self.__completed is None and ship is not self:
            packer = self.__packer
            assert isinstance(packer, Packer), 'packer error: %s' % packer
            assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
            fragments = ship.fragments
            assert fragments is not None and len(fragments) > 0, 'fragments error: %s' % ship
            for item in fragments:
                self.__completed = packer.insert(fragment=item)
        if self.__completed is not None:
            return self


class PackageDeparture(DepartureShip):

    def __init__(self, pack: Package, priority: int = 0, delegate: Optional[ShipDelegate] = None):
        super().__init__(priority=priority, delegate=delegate)
        self.__completed = pack
        self.__packages = self._split_package(pack=pack)
        self.__fragments: List[bytes] = []

    # noinspection PyMethodMayBeStatic
    def _split_package(self, pack: Package) -> List[Package]:
        if pack.head.data_type.is_message:
            return Packer.split(package=pack)
        else:
            return [pack]

    @property
    def package(self) -> Package:
        return self.__completed

    @property  # Override
    def sn(self) -> TransactionID:
        return self.__completed.head.sn

    @property  # Override
    def fragments(self) -> List[bytes]:
        if len(self.__fragments) == 0 and len(self.__packages) > 0:
            for item in self.__packages:
                self.__fragments.append(item.get_bytes())
        return self.__fragments

    # Override
    def check_response(self, ship: Arrival) -> bool:
        count = 0
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        fragments = ship.fragments
        if fragments is None:
            # it's a completed data package
            pack = ship.package
            if self.__remove_page(index=pack.head.index):
                count += 1
        else:
            for pack in fragments:
                if self.__remove_page(index=pack.head.index):
                    count += 1
        if count > 0:
            self.__fragments.clear()
            return True

    def __remove_page(self, index: int) -> bool:
        for pack in self.__packages:
            if pack.head.index == index:
                # got it
                self.__packages.remove(pack)
                return True


class PackageDocker(StarDocker):

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
    def delegate(self) -> ShipDelegate:
        gate = self.gate
        if gate is not None:
            return gate.delegate

    # noinspection PyMethodMayBeStatic
    def _parse_package(self, data: Optional[bytes]) -> Optional[Package]:
        if data is not None and len(data) > 0:
            return Package.parse(data=Data(buffer=data))

    # noinspection PyMethodMayBeStatic
    def _create_arrival(self, pack: Package) -> Arrival:
        return PackageArrival(pack=pack)

    # noinspection PyMethodMayBeStatic
    def _create_departure(self, pack: Package, priority: int = 0, delegate: Optional[ShipDelegate] = None) -> Departure:
        return PackageDeparture(pack=pack, priority=priority, delegate=delegate)

    # Override
    def get_arrival(self, data: bytes) -> Optional[Arrival]:
        pack = self._parse_package(data=data)
        if pack is not None and pack.body.size > 0:
            return self._create_arrival(pack=pack)

    # Override
    def check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        pack = ship.package
        if pack is None:
            fragments = ship.fragments
            if fragments is None or len(fragments) == 0:
                raise ValueError('fragments error: %s' % ship)
            # each ship can carry one fragment only
            pack = fragments[0]
        # check data type in package header
        head = pack.head
        body = pack.body
        data_type = head.data_type
        if data_type.is_command_response:
            # process CommandResponse
            #       'PONG'
            #       'OK'
            self.check_response(ship=ship)
            if body == PONG or body == OK:
                # command responded
                return None
            # extra data in CommandResponse?
            # let the caller to process it
        elif data_type.is_command:
            # process Command:
            #       'PING'
            #       '...'
            if body == PING:
                # PING -> PONG
                self._respond_command(sn=head.sn, body=PONG)
                return None
            else:
                # respond for Command
                self._respond_command(sn=head.sn, body=OK)
            # Unknown Command?
            # let the caller to process it
        elif data_type.is_message_response:
            # process MessageResponse
            #       'OK'
            #       'AGAIN'
            if body == AGAIN:
                # TODO: reset retries?
                return None
            self.check_response(ship=ship)
            if body == OK:
                # message responded
                return None
            # extra data in MessageResponse?
            # let the caller to process it
        else:
            # respond for Message/Fragment
            self._respond_message(sn=head.sn, pages=head.pages, index=head.index)
            if data_type.is_message_fragment:
                # assemble MessageFragment with cached fragments to completed Message
                # let the caller to process the completed message
                return self.assemble_arrival(ship=ship)
            assert data_type.is_message, 'unknown data type: %s' % data_type
            # let the caller to process the message

        if body.size == 4:
            if body == NOOP:
                # do nothing
                return None
            elif body == PING or body == PONG:
                # FIXME: these bodies should be in a Command
                # ignore them
                return None
        return ship

    # Override
    def next_departure(self, now: int) -> Optional[Departure]:
        outgo = super().next_departure(now=now)
        if outgo is not None and outgo.retries < DepartureShip.MAX_RETRIES:
            # put back for next retry
            self.append_departure(ship=outgo)
        return outgo

    # protected
    def _respond_command(self, sn: TransactionID, body: bytes):
        pack = Package.new(data_type=DataType.COMMAND_RESPONSE, sn=sn, body=Data(buffer=body))
        self.send_package(pack=pack)

    # protected
    def _respond_message(self, sn: TransactionID, pages: int, index: int):
        pack = Package.new(data_type=DataType.MESSAGE_RESPONSE, sn=sn, pages=pages, index=index, body=Data(buffer=OK))
        self.send_package(pack=pack)

    def send_package(self, pack: Package, priority: Optional[int] = 0, delegate: Optional[ShipDelegate] = None):
        ship = self._create_departure(pack=pack, priority=priority, delegate=delegate)
        self.append_departure(ship=ship)

    # Override
    def pack(self, payload: bytes, priority: int = 0, delegate: Optional[ShipDelegate] = None) -> Departure:
        pkg = Package.new(data_type=DataType.MESSAGE, body=Data(buffer=payload))
        return self._create_departure(pack=pkg, priority=priority, delegate=delegate)

    # Override
    def heartbeat(self):
        pkg = Package.new(data_type=DataType.COMMAND, body=Data(buffer=PING))
        outgo = self._create_departure(pack=pkg, priority=DeparturePriority.SLOWER)
        self.append_departure(ship=outgo)


PING = b'PING'
PONG = b'PONG'
NOOP = b'NOOP'
OK = b'OK'
AGAIN = b'AGAIN'
