# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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
from typing import Optional

from .command import LocationValue


class Session:

    EXPIRES = 120

    def __init__(self, location: LocationValue):
        super().__init__()
        self.__location = location
        self.__address: tuple = None
        self.last_time: float = 0

    @property
    def location(self) -> LocationValue:
        """ Source Address, Mapped Address, Relayed Address """
        return self.__location

    @property
    def address(self) -> Optional[tuple]:
        """ Connected Address """
        return self.__address

    @property
    def is_expired(self) -> bool:
        return (self.last_time + self.EXPIRES) < time.time()

    def matches(self, location: LocationValue=None, address: tuple=None) -> bool:
        if location is not None:
            if not self.__match_location(location=location):
                return False
        if address is not None:
            if not self.__match_address(address=address):
                return False
        return True

    def __match_location(self, location: LocationValue) -> bool:
        if self.location.source_address == location.source_address:
            if self.location.mapped_address == location.mapped_address:
                return True

    def __match_address(self, address: tuple) -> bool:
        # check connected address
        if self.address == address:
            return True
        # check source address
        source_address = self.location.source_address
        if source_address is not None:
            if (source_address.ip, source_address.port) == address:
                return True
        # check mapped address
        mapped_address = self.location.mapped_address
        if mapped_address is not None:
            if (mapped_address.ip, mapped_address.port) == address:
                return True

    def update_address(self, address: tuple) -> bool:
        # 1st, check source address
        source_address = self.location.source_address
        if source_address is not None:
            if (source_address.ip, source_address.port) == self.__address:
                # already connected to source address
                return self.__address == address
            if (source_address.ip, source_address.port) == address:
                self.__address = address
                return True
        # 2nd, check mapped address
        mapped_address = self.location.mapped_address
        if mapped_address is not None:
            if (mapped_address.ip, mapped_address.port) == self.__address:
                # already connected to mapped address
                return self.__address == address
            if (mapped_address.ip, mapped_address.port) == address:
                self.__address = address
                return True
        # # 3rd, check relayed address
        # relayed_address = self.location.relayed_address
        # if relayed_address is not None:
        #     if (relayed_address.ip, relayed_address.port) == self.__address:
        #         # connected to relayed address
        #         return self.__address == address
        #     if (relayed_address.ip, relayed_address.port) == address:
        #         self.__address = address
        #         return True
        # assert False, 'failed to update address: %s -> %s' % (address, self.identifier)


class Contact:

    def __init__(self, identifier: str):
        super().__init__()
        self.__id = identifier
        self.__sessions = []

    @property
    def identifier(self) -> str:
        return self.__id

    @property
    def is_online(self) -> bool:
        """ check whether there is any session not expired """
        for item in self.__sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            if not item.is_expired:
                return True

    @property
    def locations(self) -> list:
        """ get all valid locations """
        array = []
        for item in self.__sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            if item.is_expired:
                continue
            array.append(item.location)
        return array

    @property
    def addresses(self) -> list:
        """ get connected addresses """
        array = []
        for item in self.__sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            if item.is_expired:
                continue
            address = item.address
            if address is not None:
                array.append(address)
        return array

    def __get_session(self, location: LocationValue):
        for item in self.__sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            if item.matches(location=location):
                return item

    def check_location(self, location: LocationValue) -> bool:
        if location.identifier != self.identifier:
            # assert False, 'location ID not match: %s, %s' % (self.identifier, location)
            return False
        session = self.__get_session(location=location)
        if session is not None and session.location.timestamp > location.timestamp:
            # expired location
            return False
        # check signature by subclass
        return True

    def update_location(self, location: LocationValue) -> bool:
        """ set location with last time """
        if self.check_location(location=location):
            session = self.__get_session(location=location)
            if session is None:
                session = Session(location=location)
                self.__sessions.append(session)
            # set last time to now
            session.last_time = time.time()
            return True

    def remove_location(self, location: LocationValue):
        if self.check_location(location=location):
            session = self.__get_session(location=location)
            if session is not None:
                self.__sessions.remove(session)
                return True

    def get_location(self, address: tuple) -> Optional[LocationValue]:
        """ get location by address """
        for item in self.__sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            if item.matches(address=address):
                return item.location

    def update_address(self, address: tuple) -> bool:
        """ set connected address """
        ok = False
        for item in self.__sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            if item.update_address(address=address):
                item.last_time = time.time()
                ok = True
                # break
        return ok
