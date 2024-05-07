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
from startrek import Departure, DepartureShip, DeparturePriority
from startrek import StarDocker

from .ba import Data
from .mtp import DataType, TransactionID, Package, Packer


class PackageArrival(ArrivalShip):

    def __init__(self, pack: Package, now: float = 0):
        super().__init__(now=now)
        # head & body of the received package (or first fragment)
        self.__head = pack.head
        self.__body = pack.body
        if self.__head.is_fragment:
            self.__packer = Packer(sn=self.__head.sn, pages=self.__head.pages)
            self.__completed = self.__packer.insert(fragment=pack)
        else:
            self.__packer = None
            self.__completed = pack

    @property
    def package(self) -> Optional[Package]:
        return self.__completed

    @property
    def fragments(self) -> Optional[List[Package]]:
        packer: Packer = self.__packer
        if packer is not None:
            return packer.fragments

    @property  # Override
    def sn(self) -> TransactionID:
        return self.__head.sn

    # Override
    def assemble(self, ship):  # -> Optional[PackageArrival]:
        if self.__completed is None and ship is not self:
            packer: Packer = self.__packer
            # assert isinstance(packer, Packer), 'packer error: %s' % packer
            # assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
            fragments = ship.fragments
            # assert fragments is not None and len(fragments) > 0, 'fragments error: %s' % ship
            for item in fragments:
                self.__completed = packer.insert(fragment=item)
        if self.__completed is None:
            # extend expired time, wait for more fragments
            return None
        else:
            # package completed
            return self


class PackageDeparture(DepartureShip):

    def __init__(self, pack: Package, priority: int = 0, max_tries: int = None):
        super().__init__(priority=priority, max_tries=max_tries)
        self.__head = pack.head
        self.__body = pack.body
        self.__completed = pack
        self.__packages = self._split_package(pack=pack)
        self.__fragments: List[bytes] = []

    # noinspection PyMethodMayBeStatic
    def _split_package(self, pack: Package) -> List[Package]:
        if pack.is_message:
            return Packer.split(package=pack)
        else:
            return [pack]

    @property
    def package(self) -> Package:
        return self.__completed

    @property  # Override
    def sn(self) -> TransactionID:
        return self.__head.sn

    @property  # Override
    def fragments(self) -> List[bytes]:
        if len(self.__fragments) == 0 and len(self.__packages) > 0:
            packages = list(self.__packages)
            for pack in packages:
                self.__fragments.append(pack.get_bytes())
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
            return len(self.__packages) == 0

    def __remove_page(self, index: int) -> bool:
        packages = list(self.__packages)
        for pack in packages:
            if pack.head.index == index:
                # got it
                self.__packages.remove(pack)
                return True

    @property
    def is_important(self) -> bool:
        head = self.__completed.head
        # Only message needs waiting response;
        # and the completed package won't be a fragment.
        return head.is_message


class PackageDocker(StarDocker):

    # noinspection PyMethodMayBeStatic
    def _parse_package(self, data: bytes) -> Optional[Package]:
        if data is not None:  # and len(data) > 0:
            return Package.parse(data=Data(buffer=data))

    # noinspection PyMethodMayBeStatic
    def _create_arrival(self, pack: Package) -> Arrival:
        return PackageArrival(pack=pack)

    # noinspection PyMethodMayBeStatic
    def _create_departure(self, pack: Package, priority: int = 0) -> Departure:
        if pack.is_message:
            # normal package
            return PackageDeparture(pack=pack, priority=priority)
        else:
            # command package needs no response, and
            # response package needs no response again,
            # so this ship will be removed immediately after sent.
            return PackageDeparture(pack=pack, priority=priority, max_tries=1)

    # Override
    def _get_arrivals(self, data: bytes) -> List[Arrival]:
        pack = self._parse_package(data=data)
        if pack is None:
            return []
        else:
            return [self._create_arrival(pack=pack)]

    # Override
    async def _check_arrival(self, ship: Arrival) -> Optional[Arrival]:
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
            await self._check_response(ship=ship)
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
                await self._respond_command(sn=head.sn, body=PONG)
                return None
            else:
                # respond for Command
                await self._respond_command(sn=head.sn, body=OK)
            # Unknown Command?
            # let the caller to process it
        elif data_type.is_message_response:
            # process MessageResponse
            #       'OK'
            #       'AGAIN'
            if body == AGAIN:
                # TODO: reset retries?
                return None
            await self._check_response(ship=ship)
            if body == OK:
                # message responded
                return None
            # extra data in MessageResponse?
            # let the caller to process it
        else:
            # respond for Message/Fragment
            await self._respond_message(sn=head.sn, pages=head.pages, index=head.index)
            if data_type.is_message_fragment:
                # assemble MessageFragment with cached fragments to completed Message
                # let the caller to process the completed message
                return self._assemble_arrival(ship=ship)
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

    #
    #   Packing
    #

    # noinspection PyMethodMayBeStatic
    def _create_command(self, body: Union[bytes, bytearray]) -> Package:
        return Package.new(data_type=DataType.COMMAND, body=Data(buffer=body))

    # noinspection PyMethodMayBeStatic
    def _create_message(self, body: Union[bytes, bytearray]) -> Package:
        return Package.new(data_type=DataType.MESSAGE, body=Data(buffer=body))

    # noinspection PyMethodMayBeStatic
    def _create_command_response(self, sn: TransactionID, body: bytes) -> Package:
        return Package.new(data_type=DataType.COMMAND_RESPONSE, sn=sn, body=Data(buffer=body))

    # noinspection PyMethodMayBeStatic
    def _create_message_response(self, sn: TransactionID, pages: int, index: int) -> Package:
        return Package.new(data_type=DataType.MESSAGE_RESPONSE, sn=sn, pages=pages, index=index, body=Data(buffer=OK))

    #
    #   Sending
    #

    # protected
    async def _respond_command(self, sn: TransactionID, body: bytes) -> bool:
        pack = self._create_command_response(sn=sn, body=body)
        return await self.send_package(pack=pack)

    # protected
    async def _respond_message(self, sn: TransactionID, pages: int, index: int) -> bool:
        pack = self._create_message_response(sn=sn, pages=pages, index=index)
        return await self.send_package(pack=pack)

    async def send_command(self, body: Union[bytes, bytearray]) -> bool:
        pack = self._create_command(body=body)
        return await self.send_package(pack=pack, priority=DeparturePriority.SLOWER)

    async def send_message(self, body: Union[bytes, bytearray]) -> bool:
        pack = self._create_message(body=body)
        return await self.send_package(pack=pack, priority=DeparturePriority.NORMAL)

    async def send_package(self, pack: Package, priority: int = 0) -> bool:
        """ send data package with priority """
        outgo = self._create_departure(pack=pack, priority=priority)
        return await self.send_ship(ship=outgo)

    # Override
    async def send_data(self, payload: Union[bytes, bytearray]) -> bool:
        return await self.send_message(body=payload)

    # Override
    async def heartbeat(self):
        await self.send_command(body=PING)


PING = b'PING'
PONG = b'PONG'
NOOP = b'NOOP'
OK = b'OK'
AGAIN = b'AGAIN'
