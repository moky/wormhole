# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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
        raise NotImplemented

    @property
    def connected(self) -> bool:
        raise NotImplemented

    @property
    def local_address(self) -> Optional[tuple]:  # (str, int)
        raise NotImplemented

    @property
    def remote_address(self) -> Optional[tuple]:  # (str, int)
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: Optional[tuple] = None) -> int:
        """
        Send data

        :param data:   outgo buffer
        :param target: remote address; can be None when it's connected
        :return: count of bytes sent, probably zero when it's non-blocking mode
        """
        raise NotImplemented

    @abstractmethod
    def close(self):
        raise NotImplemented

    @property
    def state(self):  # -> ConnectionState:
        raise NotImplemented


class Delegate(ABC):
    """ Connection Delegate """

    @abstractmethod
    def connection_state_changing(self, connection: Connection, current_state, next_state):
        """
        Call when connection status is going to change

        :param connection:    current connection
        :param current_state: current state
        :param next_state     new state
        """
        raise NotImplemented

    @abstractmethod
    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload):
        """
        Call when connection received data

        :param connection: current connection
        :param remote:     remote address
        :param wrapper:    received data header (Header or None)
        :param payload:    received data body (bytes, bytearray or ByteArray)
        """
        raise NotImplemented
