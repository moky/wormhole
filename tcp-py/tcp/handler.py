# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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

import socket
import time
from abc import ABC, abstractmethod
from typing import Optional

from .status import ConnectionStatus
from .connection import Connection


class ConnectionHandler(ABC):

    # @abstractmethod
    def connection_status_changed(self, connection: Connection,
                                  old_status: ConnectionStatus, new_status: ConnectionStatus):
        """
        Call when connection status changed

        :param connection: current connection
        :param old_status: status before
        :param new_status: status after
        """
        pass

    @abstractmethod
    def connection_received_data(self, connection: Connection):
        """
        Call when received data from a connection

        :param connection: current connection
        """
        pass

    # @abstractmethod
    def connection_overflowed(self, connection: Connection, ejected: bytes):
        """
        Call when connection's cache is full

        :param connection: current connection
        :param ejected:    dropped data
        :return:
        """
        pass


#
#   Connection for Server Node
#

class ServerConnection(Connection):

    def __init__(self, sock: socket.socket):
        address = sock.getpeername()
        super().__init__(address=address, sock=sock)

    def _read(self) -> Optional[bytes]:
        try:
            return super()._read()
        except socket.error as error:
            print('[TCP] failed to receive data: %s' % error)
            self.stop()

    def _write(self, data: bytes) -> int:
        try:
            return super()._write(data=data)
        except socket.error as error:
            print('[TCP] failed to receive data: %s' % error)
            self.stop()
            return -1


#
#   Connection for Client Node
#

class ClientConnection(Connection):

    def __init__(self, address: tuple):
        super().__init__(address=address)

    def __connect(self) -> int:
        if self.socket is not None:
            # connected
            return 0
        self.status = ConnectionStatus.Connecting
        try:
            sock = socket.socket()
            sock.connect(self.address)
            self.status = ConnectionStatus.Connected
            return 0
        except socket.error as error:
            print('[TCP] failed to connect server: %s, %s' % (self.address, error))
            self.status = ConnectionStatus.Error
            return -1

    def _read(self) -> Optional[bytes]:
        # 0. check current connection
        if self.__connect() < 0:
            return None
        # 1. try to read from current connection
        try:
            return super()._read()
        except socket.error as error:
            print('[TCP] failed to read data: %s' % error)
            self.socket = None
        # 2. try to reconnect
        time.sleep(0.5)
        if self.__connect() < 0:
            return None
        # 3. try to read from new connection
        try:
            return super()._read()
        except socket.error as error:
            print('[TCP] failed to read data again: %s' % error)
            self.socket = None
        time.sleep(0.2)
        return None

    def _write(self, data: bytes) -> int:
        # 0. check current connection
        if self.__connect() < 0:
            return -1
        # 1. try to read from current connection
        try:
            return super()._write(data=data)
        except socket.error as error:
            print('[TCP] failed to write data: %s' % error)
            self.socket = None
        # 2. try to reconnect
        time.sleep(0.5)
        if self.__connect() < 0:
            return -1
        # 3. try to read from new connection
        try:
            return super()._write(data=data)
        except socket.error as error:
            print('[TCP] failed to write data again: %s' % error)
            self.socket = None
        time.sleep(0.2)
        return -1
