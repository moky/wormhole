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

from startrek.types import Address, AddressPairMap
from startrek import Channel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import PacketChannel


class ChannelPool(AddressPairMap[Channel]):

    # Override
    def get(self, remote: Optional[Address], local: Optional[Address]) -> Optional[Channel]:
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
    def set(self, remote: Optional[Address], local: Optional[Address], item: Optional[Channel]):
        old = self.get(remote=remote, local=local)
        if old is not None and old is not item:
            self.remove(remote=remote, local=local, item=old)
        super().set(remote=remote, local=local, item=item)

    # Override
    def remove(self, remote: Optional[Address], local: Optional[Address], item: Optional[Channel]) -> Optional[Channel]:
        cached = super().remove(remote=remote, local=local, item=item)
        if cached is not None:
            if not cached.closed:
                cached.close()
            return cached


class PacketHub(BaseHub, ABC):
    """ Base Datagram Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__channel_pool = self._create_channel_pool()

    # noinspection PyMethodMayBeStatic
    def _create_channel_pool(self):
        return ChannelPool()

    def bind(self, address: Address = None, host: str = None, port: int = 0):
        if address is None:
            assert port > 0, 'address error: (%s:%d)' % (host, port)
            address = (host, port)
        channel = self._get_channel(remote=None, local=address)
        if channel is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setblocking(True)
            sock.bind(address)
            sock.setblocking(False)
            channel = self._create_channel(remote=None, local=address, sock=sock)
            self._set_channel(remote=None, local=address, channel=channel)

    #
    #   Channel
    #

    # noinspection PyMethodMayBeStatic
    def _create_channel(self, remote: Optional[Address], local: Optional[Address], sock: socket.socket) -> Channel:
        # override for user-customized channel
        return PacketChannel(remote=remote, local=local, sock=sock)

    # Override
    def _all_channels(self) -> Iterable[Channel]:
        """ get a copy of all channels """
        return self.__channel_pool.items

    # Override
    def _remove_channel(self, remote: Optional[Address], local: Optional[Address], channel: Optional[Channel]):
        """ remove cached channel """
        self.__channel_pool.remove(remote=remote, local=local, item=channel)

    def _get_channel(self, remote: Optional[Address], local: Optional[Address]) -> Optional[Channel]:
        """ get cached channel """
        return self.__channel_pool.get(remote=remote, local=local)

    def _set_channel(self, remote: Optional[Address], local: Optional[Address], channel: Channel):
        """ cache channel """
        self.__channel_pool.set(remote=remote, local=local, item=channel)

    # Override
    def open(self, remote: Optional[Address], local: Optional[Address]) -> Optional[Channel]:
        # get channel with direction (remote, local)
        return self._get_channel(remote=remote, local=local)


class ServerHub(PacketHub):
    """ Datagram Server Hub """

    # Override
    def _create_connection(self, remote: Address, local: Optional[Address], channel: Channel) -> Optional[Connection]:
        conn = BaseConnection(remote=remote, local=local, channel=channel)
        conn.delegate = self.delegate  # gate
        conn.start()  # start FSM
        return conn


class ClientHub(PacketHub):
    """ Datagram Client Hub """

    # Override
    def _create_connection(self, remote: Address, local: Optional[Address], channel: Channel) -> Optional[Connection]:
        conn = ActiveConnection(remote=remote, local=None, channel=channel, hub=self)
        conn.delegate = self.delegate  # gate
        conn.start()  # start FSM
        return conn
