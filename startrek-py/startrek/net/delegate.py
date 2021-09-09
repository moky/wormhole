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

from .connection import Connection
from .state import ConnectionState


class Delegate(ABC):
    """ Connection Delegate """

    @abstractmethod
    def connection_state_changed(self, connection: Connection,
                                 previous: ConnectionState, current: ConnectionState):
        """
        Called when connection status is going to change

        :param connection: current connection
        :param previous:   old state
        :param current:    new state
        """
        raise NotImplemented

    @abstractmethod
    def connection_received(self, connection: Connection,
                            source: tuple, destination: Optional[tuple], data: bytes):
        """
        Called when connection received data

        :param connection:  current connection
        :param source:      remote address
        :param destination: local address
        :param data:        received data package
        """
        raise NotImplemented

    @abstractmethod
    def connection_sent(self, connection: Connection,
                        source: Optional[tuple], destination: tuple, data: bytes):
        """
        Called after data sent

        :param connection:  current connection
        :param source:      local address
        :param destination: remote address
        :param data:        sent data package
        """
        raise NotImplemented

    @abstractmethod
    def connection_error(self, connection: Connection,
                         source: Optional[tuple], destination: Optional[tuple], data: Optional[bytes],
                         error):
        """
        Called when connection error

        :param connection:  current connection
        :param source:      local address
        :param destination: remote address
        :param data:        sent data package
        :param error:       error message
        """
        raise NotImplemented
