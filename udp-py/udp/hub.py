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
from typing import Optional, Iterable

from startrek.types import SocketAddress, AddressPairMap
from startrek.skywalker import Runner
from startrek import Channel, BaseChannel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import PacketChannel


class ChannelPool(AddressPairMap[Channel]):

    # Override
    def get(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        assert not (remote is None and local is None), 'both addresses are empty'
        # -- Step 1 --
        #     (remote, local)
        #         this step will get the channel connected to the remote address
        #         and bound to the local address at the same time;
        #     (null, local)
        #         this step will get a channel bound to the local address, and
        #         surely not connected;
        #     (remote, null)
        #         this step will get a channel connected to the remote address,
        #         no matter which local address to be bound;
        channel = super().get(remote=remote, local=local)
        if channel is not None:
            return channel
        elif remote is None:
            # failed to get a channel bound to the local address
            return None
        # -- Step 2 --
        #     (remote, local)
        #         try to get a channel which bound to the local address, but
        #         not connected to any remote address;
        #     (null, local)
        #         this situation has already done at step 1;
        if local is not None:
            # ignore the remote address
            channel: Channel = super().get(remote=None, local=local)
            if channel is not None and channel.remote_address is None:
                # got a channel not connected yet
                return channel
        # -- Step 3 --
        #     (remote, null)
        #         try to get a channel that bound to any local address, but
        #         not connected yet;
        array = self.items
        for item in array:
            if item.remote_address is None:
                return item
        # not found

    # Override
    def set(self, item: Optional[Channel],
            remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        # 1. remove cached item
        cached = super().remove(item=item, remote=remote, local=local)
        if cached is not None and cached is not item:
            Runner.async_task(coro=cached.close())
        # 2. set new item
        old = super().set(item=item, remote=remote, local=local)
        assert old is None, 'should not happen: %s' % old
        return cached

    # Override
    def remove(self, item: Optional[Channel],
               remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        cached = super().remove(item=item, remote=remote, local=local)
        if cached is not None and cached is not item:
            Runner.async_task(coro=cached.close())
        if item is not None:
            Runner.async_task(coro=item.close())
        return cached


# noinspection PyAbstractClass
class PacketHub(BaseHub, ABC):
    """ Base Datagram Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__channel_pool = self._create_channel_pool()

    # noinspection PyMethodMayBeStatic
    def _create_channel_pool(self):
        return ChannelPool()

    async def bind(self, address: SocketAddress = None, host: str = None, port: int = 0):
        if address is None:
            assert host is not None and port > 0, 'address error: (%s:%d)' % (host, port)
            address = (host, port)
        channel = self.__channel_pool.get(remote=None, local=address)
        if channel is None:
            channel = self._create_channel(remote=None, local=address)
            assert isinstance(channel, BaseChannel), 'channel error: %s, %s' % (address, channel)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setblocking(True)
            sock.bind(address)
            sock.setblocking(False)
            # set socket for this channel
            await channel.set_socket(sock=sock)
            self.__channel_pool.set(item=channel, remote=None, local=address)

    #
    #   Channel
    #

    # noinspection PyMethodMayBeStatic
    def _create_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Channel:
        # override for user-customized channel
        return PacketChannel(remote=remote, local=local)

    # Override
    def _all_channels(self) -> Iterable[Channel]:
        """ get a copy of all channels """
        return self.__channel_pool.items

    # Override
    def _remove_channel(self, channel: Optional[Channel],
                        remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        """ remove cached channel """
        return self.__channel_pool.remove(item=channel, remote=remote, local=local)

    def _get_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        """ get cached channel """
        return self.__channel_pool.get(remote=remote, local=local)

    def _set_channel(self, channel: Channel,
                     remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        """ cache channel """
        return self.__channel_pool.set(item=channel, remote=remote, local=local)


class ServerHub(PacketHub):
    """ Datagram Server Hub """

    # Override
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        conn = BaseConnection(remote=remote, local=local)
        conn.delegate = self.delegate  # gate
        return conn

    # Override
    async def open(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        # get channel with direction (remote, local)
        return self._get_channel(remote=remote, local=local)


class ClientHub(PacketHub):
    """ Datagram Client Hub """

    # Override
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        conn = ActiveConnection(remote=remote, local=local)
        conn.delegate = self.delegate  # gate
        return conn

    # Override
    async def open(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        # get channel with direction (remote, local)
        return self._get_channel(remote=remote, local=local)
