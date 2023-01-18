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
import time
import weakref
from abc import ABC, abstractmethod
from typing import Optional, Iterable

from ..types import Address, AddressPairMap
from ..net import Hub, Channel, Connection, ConnectionDelegate


class ConnectionPool(AddressPairMap[Connection]):

    # Override
    def set(self, remote: Optional[Address], local: Optional[Address], item: Optional[Connection]):
        old = self.get(remote=remote, local=local)
        if old is not None and old is not item:
            self.remove(remote=remote, local=local, item=old)
        super().set(remote=remote, local=local, item=item)

    # Override
    def remove(self, remote: Optional[Address], local: Optional[Address],
               item: Optional[Connection]) -> Optional[Connection]:
        cached = super().remove(remote=remote, local=local, item=item)
        if cached is not None:
            if not cached.closed:
                cached.close()
            return cached


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
        self.__connection_pool = self._create_connection_pool()
        self.__last_time_drive_connection = time.time()

    # noinspection PyMethodMayBeStatic
    def _create_connection_pool(self):
        return ConnectionPool()

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    #
    #   Channel
    #

    @abstractmethod
    def _all_channels(self) -> Iterable[Channel]:
        """
        get all channels

        :return: copy of channels
        """
        raise NotImplemented

    @abstractmethod
    def _remove_channel(self, remote: Optional[Address], local: Optional[Address], channel: Optional[Channel]):
        """
        remove socket channel

        :param remote:  remote address
        :param local:   local address
        :param channel: socket channel
        """
        raise NotImplemented

    #
    #   Connection
    #

    @abstractmethod
    def _create_connection(self, remote: Address, local: Optional[Address], channel: Channel) -> Optional[Connection]:
        """
        create connection with channel channel & addresses

        :param channel: channel channel
        :param remote:  remote address
        :param local:   local address
        :return: None on channel not exists
        """
        raise NotImplemented

    def _all_connections(self) -> Iterable[Connection]:
        """ get a copy of all connections """
        return self.__connection_pool.items

    def _get_connection(self, remote: Address, local: Optional[Address]) -> Optional[Connection]:
        """ get cached connection """
        return self.__connection_pool.get(remote=remote, local=local)

    def _set_connection(self, remote: Address, local: Optional[Address], connection: Connection):
        """ cache connection """
        self.__connection_pool.set(remote=remote, local=local, item=connection)

    def _remove_connection(self, remote: Address, local: Optional[Address], connection: Optional[Connection]):
        """ remove cached connection """
        self.__connection_pool.remove(remote=remote, local=local, item=connection)

    # Override
    def connect(self, remote: Address, local: Optional[Address] = None) -> Optional[Connection]:
        conn = self._get_connection(remote=remote, local=local)
        if conn is not None:
            # check local address
            if local is None:
                return conn
            address = conn.local_address
            if address is None or address == local:
                return conn
            # local address not matched? ignore this connection
        # try to open channel with direction (remote, local)
        channel = self.open(remote=remote, local=local)
        if channel is None or channel.closed:
            return None
        # create with channel
        conn = self._create_connection(remote=remote, local=local, channel=channel)
        if conn is not None:
            # cache connection for (remote, local)
            self._set_connection(remote=conn.remote_address, local=conn.local_address, connection=conn)
            return conn

    #
    #   Process
    #

    def _drive_channel(self, channel: Channel) -> bool:
        if not channel.alive:
            # cannot drive closed channel
            return False
        # try to receive
        try:
            data, remote = channel.receive(max_len=self.MSS)
        except socket.error as error:
            remote = channel.remote_address
            local = channel.local_address
            delegate = self.delegate
            if delegate is None or remote is None:
                # UDP channel may not connected
                # so no connection for it
                self._remove_channel(remote=remote, local=local, channel=channel)
            else:
                # remove channel and callback with connection
                conn = self._get_connection(remote=remote, local=local)
                self._remove_channel(remote=remote, local=local, channel=channel)
                if conn is not None:
                    delegate.connection_error(error=error, connection=conn)
            return False
        if remote is None:
            # received nothing
            return False
        else:
            local = channel.local_address
        # get connection for processing received data
        conn = self.connect(remote=remote, local=local)
        if conn is not None:
            conn.received(data=data)
        return True

    def _drive_channels(self, channels: Iterable[Channel]) -> int:
        count = 0
        for sock in channels:
            # drive channel to receive data
            if self._drive_channel(channel=sock):
                count += 1
        return count

    # noinspection PyMethodMayBeStatic
    def _drive_connections(self, connections: Iterable[Connection]):
        now = time.time()
        elapsed = now - self.__last_time_drive_connection
        for conn in connections:
            # drive connection to go on
            conn.tick(now=now, elapsed=elapsed)
            # NOTICE: let the delegate to decide whether close an error connection
            #         or just remove it.
        self.__last_time_drive_connection = now

    def _cleanup_channels(self, channels: Iterable[Channel]):
        for sock in channels:
            if not sock.alive:
                # if channel not connected (TCP) and not bound (UDP),
                # means it's closed, remove it from the hub
                self._remove_channel(remote=sock.remote_address, local=sock.local_address, channel=sock)

    def _cleanup_connections(self, connections: Iterable[Connection]):
        # NOTICE: multi connections may share same channel (UDP Hub)
        for conn in connections:
            if conn.closed:
                # if connection closed, remove it from the hub; notice that
                # ActiveConnection can reconnect, it'll be not connected
                # but still open, don't remove it in this situation.
                self._remove_connection(remote=conn.remote_address, local=conn.local_address, connection=conn)

    # Override
    def process(self) -> bool:
        # 1. drive all channels to receive data
        channels = self._all_channels()
        count = self._drive_channels(channels=channels)
        # 2. drive all connections to move on
        connections = self._all_connections()
        self._drive_connections(connections=connections)
        # 3. cleanup closed channels and connections
        self._cleanup_channels(channels=channels)
        self._cleanup_connections(connections=connections)
        return count > 0
