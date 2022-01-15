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

from ..types import Address
from ..fsm import Ticker


class Connection(Ticker, ABC):

    #
    #   Flags
    #

    @property
    def opened(self) -> bool:
        """ not closed """
        raise NotImplemented

    @property
    def bound(self) -> bool:
        """ is_bound() """
        raise NotImplemented

    @property
    def connected(self) -> bool:
        """ is_connected() """
        raise NotImplemented

    @property
    def alive(self) -> bool:
        """ is_opened() and (is_connected() or is_bound()) """
        raise NotImplemented

    @property
    def local_address(self) -> Optional[Address]:  # (str, int)
        raise NotImplemented

    @property
    def remote_address(self) -> Optional[Address]:  # (str, int)
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: Optional[Address] = None) -> int:
        """
        Send data

        :param data:   outgo buffer
        :param target: remote address; can be None when it's connected
        :return: count of bytes sent, probably zero when it's non-blocking mode
        """
        raise NotImplemented

    @abstractmethod
    def received(self, data: bytes, remote: Optional[Address], local: Optional[Address]):
        """
        Process received data

        :param data:   received data
        :param remote: remote address
        :param local:  local address
        """
        raise NotImplemented

    @abstractmethod
    def close(self):
        """ Close the connection """
        raise NotImplemented

    @property
    def state(self):  # -> ConnectionState:
        """ Get connection state """
        raise NotImplemented
