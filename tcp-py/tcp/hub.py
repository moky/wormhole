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

import socket
import threading
import time
from abc import ABC
from typing import Optional, Iterable

from startrek.types import SocketAddress, AddressPairMap
from startrek.skywalker import Runnable, Runner, Daemon
from startrek import Channel, BaseChannel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .aio import is_blocking
from .channel import StreamChannel


class ChannelPool(AddressPairMap[Channel]):

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
class StreamHub(BaseHub, ABC):
    """ Base Stream Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__channel_pool = self._create_channel_pool()

    # noinspection PyMethodMayBeStatic
    def _create_channel_pool(self):
        return ChannelPool()

    #
    #   Channel
    #

    # noinspection PyMethodMayBeStatic
    def _create_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Channel:
        """ create channel with socket & addresses """
        return StreamChannel(remote=remote, local=local)

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


class ServerHub(StreamHub, Runnable):
    """ Stream Server Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__local = None   # SocketAddress
        self.__master = None  # socket.socket
        self.__daemon = Daemon(target=self)
        self.__running = False

    # Override
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        conn = BaseConnection(remote=remote, local=local)
        conn.delegate = self.delegate  # gate
        return conn

    async def bind(self, address: Optional[SocketAddress] = None, host: Optional[str] = None, port: Optional[int] = 0):
        if address is None:
            if port > 0:
                assert host is not None, 'host should not be empty'
                address = (host, port)
            else:
                address = self.__local
                assert address is not None, 'local address not set'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(True)
        sock.bind(address)
        sock.listen(1)
        # sock.setblocking(False)
        self._set_master(master=sock)
        self.__local = address

    def _get_master(self) -> Optional[socket.socket]:
        return self.__master

    def _set_master(self, master: socket.socket):
        # 1. replace with new socket
        old = self.__master
        self.__master = master
        # 2. close old socket
        if not (old is None or old is master):
            old.close()

    @property
    def local_address(self) -> Optional[SocketAddress]:
        return self.__local

    #
    #   Threading
    #

    @property
    def running(self) -> bool:
        return self.__running

    async def start(self):
        assert not self.__running, 'server hub is running: %s' % self
        # 1. mark this hub to running
        self.__running = True
        # 2. start an async task for this hub
        self.__daemon.start()
        # await self.run()

    async def stop(self):
        # 1. mark this hub to stopped
        self.__running = False
        # 2. waiting for the hub to stop
        await Runner.sleep(seconds=0.25)
        # 3. cancel the async task
        self.__daemon.stop()

    # Override
    async def run(self):
        self.__running = True
        while self.running:
            master = self._get_master()
            try:
                sock, address = master.accept()
                if sock is None:
                    await Runner.sleep(seconds=Runner.INTERVAL_NORMAL)
                else:
                    await self._accept(remote=address, local=self.local_address, sock=sock)
            except socket.error as error:
                if error.errno == socket.EAGAIN:  # error.strerror == 'Resource temporarily unavailable':
                    if not await is_blocking(sock=master):
                        continue
                print('[TCP] socket error: %s' % error)
            except Exception as error:
                print('[TCP] accept error: %s' % error)

    async def _accept(self, remote: SocketAddress, local: SocketAddress, sock: socket.socket):
        # override for user-customized channel
        channel = self._create_channel(remote=remote, local=local)
        assert isinstance(channel, BaseChannel), 'channel error: %s, %s' % (remote, channel)
        # set socket for this channel
        sock.setblocking(False)
        await channel.set_socket(sock=sock)
        self._set_channel(channel=channel, remote=channel.remote_address, local=channel.local_address)

    # Override
    async def open(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        assert remote is not None, 'remote address empty: %s, %s' % (remote, local)
        return self._get_channel(remote=remote, local=local)


class ClientHub(StreamHub):
    """ Stream Client Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__lock = threading.Lock()

    # Override
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        conn = ActiveConnection(remote=remote, local=local)
        conn.delegate = self.delegate  # gate
        return conn

    # Override
    async def open(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        assert remote is not None, 'remote address empty: %s, %s' % (remote, local)
        # try to get channel
        with self.__lock:
            old = self._get_channel(remote=remote, local=local)
            if old is None:
                # create channel with socket
                channel = self._create_channel(remote=remote, local=local)
                self._set_channel(channel, remote=remote, local=local)
            else:
                channel = old
        if old is None:
            # initialize socket
            sock = await create_socket(remote=remote, local=local)
            if sock is None:
                print('[TCP] failed to prepare socket: %s -> %s' % (local, remote))
                self._remove_channel(channel, remote=remote, local=local)
                channel = None
            else:
                assert isinstance(channel, BaseChannel), 'channel error: %s, %s' % (remote, channel)
                # set socket for this channel
                await channel.set_socket(sock=sock)
        return channel


async def create_socket(remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[socket.socket]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
        sock.setblocking(True)
        # try to bind
        if local is not None:
            sock.bind(local)
        # try to connect
        sock.connect(remote)
        sock.setblocking(False)
        return sock
    except socket.error as error:
        print('[TCP] %s > failed to create socket %s -> %s: %s' % (current_time(), local, remote, error))


def current_time() -> str:
    now = time.time()
    localtime = time.localtime(now)
    return time.strftime('%Y-%m-%d %H:%M:%S', localtime)
