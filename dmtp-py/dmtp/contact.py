# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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
from abc import ABC, abstractmethod
from typing import Optional

from .command import LocationValue


class Session:

    def __init__(self, location: LocationValue, address: tuple):
        super().__init__()
        self.__location = location
        self.__address = address

    @property
    def location(self) -> LocationValue:
        return self.__location

    @property
    def address(self) -> tuple:
        return self.__address


class ContactDelegate(ABC):

    @abstractmethod
    def sign_location(self, location: LocationValue) -> Optional[LocationValue]:
        """
        Sign location addresses and time

        :param location: location info with 'MAPPED-ADDRESS' from server
        :return: signed location info
        """
        raise NotImplemented

    @abstractmethod
    def current_location(self) -> Optional[LocationValue]:
        """
        Get my location

        :return: my current location
        """
        raise NotImplemented

    @abstractmethod
    def get_location(self, address: tuple) -> Optional[LocationValue]:
        """
        Get location info by address

        :param address: IP and port
        :return: location info bond to this address
        """
        raise NotImplemented

    @abstractmethod
    def get_locations(self, identifier: str) -> list:
        """
        Get locations list by ID

        :param identifier: user ID
        :return: all locations of this user, ordered by time
        """
        raise NotImplemented

    @abstractmethod
    def update_location(self, location: LocationValue) -> bool:
        """
        Check and update location info

        :param location: location info with ID and signature, time
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def remove_location(self, location: LocationValue) -> bool:
        """
        Check and remove location info

        :param location: location info with ID and signature, time
        :return: False on error
        """
        raise NotImplemented


class Contact:

    def __init__(self, identifier: str):
        super().__init__()
        self.__id = identifier
        self.__locations = []  # ordered by time
        self.__locations_lock = threading.Lock()

    @property
    def identifier(self) -> str:
        return self.__id

    @property
    def locations(self) -> list:
        """ Get all locations ordered by time """
        with self.__locations_lock:
            return self.__locations.copy()

    def get_location(self, address: tuple) -> Optional[LocationValue]:
        """ Get location by (IP, port) """
        with self.__locations_lock:
            host = address[0]
            port = address[1]
            for item in self.__locations:
                assert isinstance(item, LocationValue), 'location error: %s' % item
                if item.source_address is not None \
                        and port == item.source_address.port \
                        and host == item.source_address.ip:
                    return item
                if item.mapped_address is not None \
                        and port == item.mapped_address.port \
                        and host == item.mapped_address.ip:
                    return item

    def update_location(self, location: LocationValue) -> bool:
        """
        When received 'HI' command, update the location in it

        :param location: location info with time
        :return: False on error
        """
        with self.__locations_lock:
            # check same location with different time
            pos = len(self.__locations)
            while pos > 0:
                pos -= 1
                item = self.__locations[pos]
                assert isinstance(item, LocationValue), 'location error: %s' % item
                if item.source_address != location.source_address:
                    continue
                if item.mapped_address != location.mapped_address:
                    continue
                if item.timestamp >= location.timestamp:
                    return False
                # remove it
                self.__locations.pop(pos)
            # insert (ordered by time)
            pos = len(self.__locations)
            while pos > 0:
                pos -= 1
                item = self.__locations[pos]
                assert isinstance(item, LocationValue), 'location error: %s' % item
                if item.timestamp <= location.timestamp:
                    # insert after it
                    pos += 1
                    break
            self.__locations.insert(pos, location)
            return True

    def remove_location(self, location: LocationValue):
        """
        When receive 'BYE' command, remove the location in it

        :param location: location info with signature and time
        """
        with self.__locations_lock:
            self.__locations.remove(location)
