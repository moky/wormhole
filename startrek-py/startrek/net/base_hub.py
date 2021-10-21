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

    @abstractmethod  # protected
    def _all_channels(self) -> Set[Channel]:
        """
        Get all channels

        :return: copy of channels
        """
        raise NotImplemented

    @abstractmethod  # protected
    def _create_connection(self, sock: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        """
        Create connection with sock channel & addresses

        :param sock:   sock channel
        :param remote: remote address
        :param local:  local address
        :return: None on channel not exists
        """
        raise NotImplemented

    # Override
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Optional[Connection]:
        conn = self.__connection_pool.get(remote=remote, local=local)
        if conn is not None:
            # check local address
            if local is None:
                return conn
            address = conn.local_address
            if address is None or address == local:
                return conn
            # local address not matched? ignore this connection
        # try to open channel with direction (remote, local)
        sock = self.open_channel(remote=remote, local=local)
        if sock is None:  # or not sock.opened:
            return None
        # create with channel
        conn = self._create_connection(sock=sock, remote=remote, local=local)
        if conn is not None:
            # NOTICE: local address in the connection may be set to None
            local = conn.local_address
            remote = conn.remote_address
            self.__connection_pool.put(remote=remote, local=local, value=conn)
            return conn

    # Override
    def disconnect(self, remote: Optional[tuple], local: Optional[tuple] = None,
                   connection: Optional[Connection] = None) -> Optional[Connection]:
        conn = self.__remove_connection(remote=remote, local=local, connection=connection)
        if conn is not None:
            conn.close()
        if connection is not None and connection is not conn:
            connection.close()
        if conn is None:
            return connection
        else:
            return conn

    def __remove_connection(self, remote: tuple = None, local: Optional[tuple] = None,
                            connection: Connection = None) -> Optional[Connection]:
        if connection is None:
            connection = self.__connection_pool.get(remote=remote, local=local)
            if connection is None:
                return None
        # check local address
        if local is not None:
            address = connection.local_address
            if address is not None and address != local:
                # local address not matched
                return None
        remote = connection.remote_address
        local = connection.local_address
        return self.__connection_pool.remove(remote=remote, local=local, value=connection)

    def _drive_channel(self, sock: Channel) -> bool:
        local = sock.local_address
        # try to receive
        try:
            data, remote = sock.receive(max_len=self.MSS)
        except socket.error as error:
            # print('[NET] failed to receive data: %s' % error)
            remote = sock.remote_address
            # socket error, remove the channel
            self.close_channel(channel=sock)
            # callback
            delegate = self.delegate
            if delegate is not None:
                delegate.connection_error(error=error, data=None, source=remote, destination=local, connection=None)
            return False
        if remote is None:
            # received nothing
            return False
        # get connection for processing received data
        conn = self.connect(remote=remote, local=local)
        if conn is not None:
            conn.received(data=data, remote=remote, local=local)
        return True

    # Override
    def process(self) -> bool:
        count = 0
        # 1. drive all channels to receive data
        channels = self._all_channels()
        for sock in channels:
            if sock.alive and self._drive_channel(sock=sock):
                # received data from this socket channel
                count += 1
        # 2. drive all connections to move on
        connections = self.__connection_pool.values
        for conn in connections:
            # drive connection to go on
            conn.tick()
            # NOTICE: let the delegate to decide whether close an error connection
            #         or just remove it.
        return count > 0
