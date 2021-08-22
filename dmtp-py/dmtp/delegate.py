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

from abc import ABC, abstractmethod
from typing import Optional, List

from .protocol import LocationValue


class LocationDelegate(ABC):

    @abstractmethod
    def store_location(self, location: LocationValue) -> bool:
        """
        Check location info; if signature matched, save it.

        :param location: location info with ID, addresses, time and signature
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def clear_location(self, location: LocationValue) -> bool:
        """
        Check location info; if signature matched, remove it.

        :param location: location info with ID, addresses, time and signature
        :return: False on error
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
    def get_locations(self, identifier: str) -> List[LocationValue]:
        """
        Get locations list by ID

        :param identifier: user ID
        :return: all locations of this user, ordered by time
        """
        raise NotImplemented

    @abstractmethod
    def sign_location(self, location: LocationValue) -> Optional[LocationValue]:
        """
        Sign location addresses and time

        :param location: location info with 'MAPPED-ADDRESS' from server
        :return: signed location info
        """
        raise NotImplemented
