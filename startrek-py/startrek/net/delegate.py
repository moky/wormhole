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

import socket
from abc import ABC, abstractmethod
from typing import Optional, Union

from .connection import Connection
from .state import ConnectionState


class ConnectionDelegate(ABC):
    """ Connection Delegate """

    @abstractmethod
    async def connection_state_changed(self, previous: Optional[ConnectionState], current: Optional[ConnectionState],
                                       connection: Connection):
        """
        Called when connection status is changed

        :param previous:   old state
        :param current:    new state
        :param connection: current connection
        """
        raise NotImplemented

    @abstractmethod
    async def connection_received(self, data: bytes, connection: Connection):
        """
        Called when connection received data

        :param data:        received data package
        :param connection:  current connection
        """
        raise NotImplemented

    @abstractmethod
    async def connection_sent(self, sent: int, data: bytes, connection: Connection):
        """
        Called after data sent via the connection

        :param sent:        length of sent bytes
        :param data:        sent data package
        :param connection:  current connection
        """
        raise NotImplemented

    @abstractmethod
    async def connection_failed(self, error: Union[IOError, socket.error], data: bytes, connection: Connection):
        """
        Called when failed to send data via the connection

        :param error:       connection error
        :param data:        outgoing data package
        :param connection:  current connection
        """
        raise NotImplemented

    @abstractmethod
    async def connection_error(self, error: Union[IOError, socket.error], connection: Connection):
        """
        Called when connection (receiving) error

        :param error:       connection error
        :param connection:  current connection
        """
        raise NotImplemented
