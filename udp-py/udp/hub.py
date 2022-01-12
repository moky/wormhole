# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
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
from abc import ABC
from typing import Optional, Set

from startrek.types import AddressPairMap
from startrek import Channel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import PackageChannel


class PackageHub(BaseHub, ABC):
    """ Base Package Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__channel_pool: AddressPairMap[Channel] = AddressPairMap()

    def bind(self, address: tuple = None, host: str = None, port: int = 0):
        if address is None:
            address = (host, port)
        channel = self._get_channel(local=address)
        if channel is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setblocking(True)
            sock.bind(address)
            sock.setblocking(False)
            channel = self._create_channel(remote=None, local=address, sock=sock)
            self._set_channel(channel=channel)

    # noinspection PyMethodMayBeStatic
    def _create_channel(self, remote: Optional[tuple], local: Optional[tuple], sock: socket.socket) -> Channel:
        # override for user-customized channel
        return PackageChannel(remote=remote, local=local, sock=sock)

    def put_channel(self, channel: Channel):
        self._set_channel(channel=channel)

    # Override
    def _all_channels(self) -> Set[Channel]:
        return self.__channel_pool.items

    def _get_channel(self, local: Optional[tuple]) -> Optional[Channel]:
        return self.__channel_pool.get(remote=None, local=local)

    def _set_channel(self, channel: Channel):
        local = channel.local_address
        # check old channel
        old = self.__channel_pool.get(remote=None, local=local)
        if old is not None and old is not channel:
            self._close_channel(channel=old)
        # set new channel
        self.__channel_pool.set(remote=None, local=local, item=channel)

    # Override
    def _remove_channel(self, channel: Channel):
        local = channel.local_address
        old = self.__channel_pool.remove(remote=None, local=local, item=channel)
        if old is not None and old is not channel:
            # should not happen
            self._close_channel(channel=old)

    # noinspection PyMethodMayBeStatic
    def _close_channel(self, channel: Channel):
        if channel.opened:
            channel.close()

    # Override
    def open(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Channel]:
        if local is None:
            # get any channel
            items = self.__channel_pool.items
            for channel in items:
                if channel is not None:
                    return channel
            # channel not found
        else:
            return self._get_channel(local=local)


class ServerHub(PackageHub):
    """ Package Server Hub """

    # Override
    def _create_connection(self, channel: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        gate = self.delegate
        conn = BaseConnection(remote=remote, local=None, channel=channel, delegate=gate, hub=self)
        conn.start()  # start FSM
        return conn


class ClientHub(PackageHub):
    """ Package Client Hub """

    # Override
    def _create_connection(self, channel: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        gate = self.delegate
        conn = ActiveConnection(remote=remote, local=None, channel=channel, delegate=gate, hub=self)
        conn.start()  # start FSM
        return conn
