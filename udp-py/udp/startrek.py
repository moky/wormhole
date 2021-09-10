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

from startrek import Arrival, ArrivalShip, Departure, DepartureShip, DeparturePriority
from startrek import GateDelegate
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
    def sn(self):
        return self.__sn

    # Override
    def assemble(self, ship):  # -> Optional[PackageArrival]:
        if self.__completed is None:
            packer = self.__packer
            assert isinstance(packer, Packer), 'packer error: %s' % packer
            assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
            fragments = ship.fragments
            assert fragments is not None and len(fragments) > 0, 'fragments error: %s' % ship
            for item in fragments:
                self.__completed = packer.insert(fragment=item)
        if self.__completed is not None:
            return PackageArrival(pack=self.__completed)


class PackageDeparture(DepartureShip):

    def __init__(self, priority: int, pack: Package):
        super().__init__(priority=priority)
        self.__completed = pack
        if pack.head.data_type.is_message:
            self.__packages = Packer.split(package=pack)
        else:
            self.__packages = [pack]
        self.__fragments: List[bytes] = []

    @property
    def package(self) -> Package:
        return self.__completed

    @property  # Override
    def sn(self):
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

    @property  # Override
    def gate(self) -> StarGate:
        return self.__gate()

    @property  # Override
    def delegate(self) -> GateDelegate:
        return self.gate.delegate

    # Override
    def get_income_ship(self, data: bytes) -> Optional[Arrival]:
        if data is None or len(data) == 0:
            # should not happen
            return None
        pack = Package.parse(data=Data(buffer=data))
        if pack is None:
            # data error
            return None
        body = pack.body
        if body is None or body.size == 0:
            # body should not be empty
            return None
        return PackageArrival(pack=pack)

    # Override
    def check_income_ship(self, ship: Arrival) -> Optional[Arrival]:
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
                self.__respond_command(sn=head.sn, body=PONG)
                return None
            # respond for Command
            self.__respond_command(sn=head.sn, body=OK)
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
        elif data_type.is_message_fragment:
            # assemble MessageFragment with cached fragments to completed Message
            ship = self.dock.assemble_arrival(ship=ship)
            # let the caller to process the completed message
        elif data_type.is_message:
            # respond for Message
            self.__respond_message(sn=head.sn, pages=head.pages, index=head.index)
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

    def __respond_command(self, sn: TransactionID, body: bytes):
        pack = Package.new(data_type=DataType.COMMAND_RESPONSE, sn=sn, body=Data(buffer=body))
        self.send_package(pack=pack)

    def __respond_message(self, sn: TransactionID, pages: int, index: int):
        pack = Package.new(data_type=DataType.MESSAGE_RESPONSE, sn=sn, pages=pages, index=index, body=Data(buffer=OK))
        self.send_package(pack=pack)

    # Override
    def send_outgo_ship(self, ship: Departure) -> bool:
        fragments = ship.fragments
        if fragments is None or len(fragments) == 0:
            return True
        assert isinstance(ship, PackageDeparture), 'departure ship error: %s' % ship
        if ship.retries < ship.MAX_RETRIES:
            # put back for next retry
            self.dock.append_departure(ship=ship)
        return super().send_outgo_ship(ship=ship)

    # Override
    def pack(self, payload: bytes, priority: int = 0) -> Departure:
        pack = Package.new(data_type=DataType.MESSAGE, body=Data(buffer=payload))
        return PackageDeparture(priority=priority, pack=pack)

    # Override
    def heartbeat(self):
        pack = Package.new(data_type=DataType.COMMAND, body=Data(buffer=PING))
        self.send_package(pack=pack, priority=DeparturePriority.SLOWER)

    def send_package(self, pack: Package, priority: Optional[int] = 0):
        ship = PackageDeparture(priority=priority, pack=pack)
        self.dock.append_departure(ship=ship)


PING = b'PING'
PONG = b'PONG'
NOOP = b'NOOP'
OK = b'OK'
AGAIN = b'AGAIN'
