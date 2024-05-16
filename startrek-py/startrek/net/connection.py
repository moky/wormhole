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

from abc import ABC, abstractmethod
from typing import Optional

from ..types import SocketAddress
from ..skywalker import Ticker


class Connection(Ticker, ABC):

    #
    #   Flags
    #

    @property
    @abstractmethod
    def closed(self) -> bool:
        """ not is_open() """
        raise NotImplemented

    @property
    @abstractmethod
    def bound(self) -> bool:
        """ is_bound() """
        raise NotImplemented

    @property
    @abstractmethod
    def connected(self) -> bool:
        """ is_connected() """
        raise NotImplemented

    @property
    @abstractmethod
    def alive(self) -> bool:
        """ is_opened() and (is_connected() or is_bound()) """
        raise NotImplemented

    @property
    @abstractmethod
    def available(self) -> bool:
        """ ready for reading """
        raise NotImplemented

    @property
    @abstractmethod
    def vacant(self) -> bool:
        """ ready for writing """
        raise NotImplemented

    @property
    @abstractmethod
    def local_address(self) -> Optional[SocketAddress]:  # (str, int)
        raise NotImplemented

    @property
    @abstractmethod
    def remote_address(self) -> Optional[SocketAddress]:  # (str, int)
        raise NotImplemented

    @property
    @abstractmethod
    def state(self):  # -> Optional[ConnectionState]:
        """ Get connection state """
        raise NotImplemented

    @abstractmethod
    async def send(self, data: bytes) -> int:
        """
        Send data

        :param data: outgo data package
        :return: count of bytes sent, probably zero when it's non-blocking mode
        """
        raise NotImplemented

    @abstractmethod
    async def received(self, data: bytes):
        """
        Call on received data for processing

        :param data: received data
        """
        raise NotImplemented

    @abstractmethod
    async def close(self):
        """ Close the connection """
        raise NotImplemented
