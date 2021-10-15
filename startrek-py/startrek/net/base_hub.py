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
import weakref
from abc import ABC, abstractmethod
from typing import Optional, Set

from ..types import AddressPairMap

from .hub import Hub
from .channel import Channel
from .connection import Connection
from .delegate import ConnectionDelegate
from .state import ConnectionState


class BaseHub(Hub, ABC):

    """
        Maximum Segment Size
        ~~~~~~~~~~~~~~~~~~~~
        Buffer size for receiving package

        MTU        : 1500 bytes (excludes 14 bytes ethernet header & 4 bytes FCS)
        IP header  :   20 bytes
        TCP header :   20 bytes
        UDP header :    8 bytes
    """
    MSS = 1472  # 1500 - 20 - 8

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)
        self.__connection_pool: AddressPairMap[Connection] = AddressPairMap()

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    @abstractmethod
    def channels(self) -> Set[Channel]:
        """ Get all channels """
        raise NotImplemented

    @abstractmethod  # protected
    def create_connection(self, sock: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        raise NotImplemented

    def __create_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        sock = self.open(remote=remote, local=local)
        if sock is None:  # or not sock.opened:
            return None
        if local is None:
            local = sock.local_address
        return self.create_connection(sock=sock, remote=remote, local=local)

    # Override
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Optional[Connection]:
        conn = self.__connection_pool.get(remote=remote, local=local)
        if conn is None:
            conn = self.__create_connection(remote=remote, local=local)
            if conn is not None:
                if local is None:
                    local = conn.local_address
                self.__connection_pool.put(remote=remote, local=local, value=conn)
        return conn

    # Override
    def disconnect(self, connection: Connection):
        remote = connection.remote_address
        local = connection.local_address
        conn = self.__connection_pool.remove(remote=remote, local=local, value=None)
        if conn is not None:
            conn.close()
        if connection is not conn:
            connection.close()

    def __close_connection(self, remote: tuple, local: Optional[tuple]):
        conn = self.__connection_pool.get(remote=remote, local=local)
        if conn is not None:
            self.__connection_pool.remove(remote=remote, local=local, value=conn)
            conn.close()

    def __drive(self, sock: Channel) -> bool:
        # try to receive
        try:
            data, remote = sock.receive(max_len=self.MSS)
        except socket.error:
            # socket error, remove the channel
            self.close(channel=sock)
            # remove connected connection
            remote = sock.remote_address
            if remote is not None:
                self.__close_connection(remote=remote, local=sock.local_address)
            return False
        if remote is None:
            # received nothing
            return False
        # get connection for processing received data
        conn = self.connect(remote=remote, local=sock.local_address)
        if conn is not None:
            conn.received(data=data)
        return True

    # Override
    def process(self) -> bool:
        count = 0
        # 1. drive all channels to receive data
        channels = self.channels()
        for sock in channels:
            if sock.opened and self.__drive(sock=sock):
                # received data from this socket channel
                count += 1
        # 2. drive all connections to move on
        connections = self.__connection_pool.values
        for conn in connections:
            # drive connection to go on
            conn.tick()
            # check connection state
            state = conn.state
            if state is None or state == ConnectionState.ERROR:
                # connection lost
                self.disconnect(connection=conn)
        return count > 0
