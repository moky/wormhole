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
from startrek.fsm import Runnable, Daemon
from startrek import Channel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import StreamChannel


class ChannelPool(AddressPairMap[Channel]):

    # Override
    def set(self, item: Optional[Channel],
            remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        # 1. remove cached item
        cached = super().remove(item=item, remote=remote, local=local)
        if cached is not None and cached is not item:
            cached.close()
        # 2. set new item
        old = super().set(item=item, remote=remote, local=local)
        assert old is None, 'should not happen'
        return cached

    # Override
    def remove(self, item: Optional[Channel],
               remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        cached = super().remove(item=item, remote=remote, local=local)
        if cached is not None and cached is not item:
            cached.close()
        if item is not None:
            item.close()
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
    def _create_channel(self, sock: socket.socket,
                        remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Channel:
        """ create channel with socket & addresses """
        return StreamChannel(sock=sock, remote=remote, local=local)

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

    # Override
    def open(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        assert remote is not None, 'remote address empty: %s, %s' % (remote, local)
        return self._get_channel(remote=remote, local=local)


class ServerHub(StreamHub, Runnable):
    """ Stream Server Hub """

    def __init__(self, delegate: ConnectionDelegate, daemonic: bool = True):
        super().__init__(delegate=delegate)
        self.__local = None   # SocketAddress
        self.__master = None  # socket.socket
        # running thread
        self.__daemon = Daemon(target=self.run, daemonic=daemonic)
        self.__running = False

    # Override
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        conn = BaseConnection(remote=remote, local=local)
        conn.delegate = self.delegate  # gate
        conn.start(hub=self)  # start FSM
        return conn

    def bind(self, address: Optional[SocketAddress] = None, host: Optional[str] = None, port: Optional[int] = 0):
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

    def start(self):
        self.stop()
        self.__running = True
        return self.__daemon.start()

    def stop(self):
        self.__running = False
        self.__daemon.stop()

    # Override
    def run(self):
        self.__running = True
        while self.running:
            try:
                master = self._get_master()
                sock, address = master.accept()
                if sock is not None:
                    self._accept(remote=address, local=self.local_address, sock=sock)
            except socket.error as error:
                print('[TCP] socket error: %s' % error)
            except Exception as error:
                print('[TCP] accept error: %s' % error)

    def _accept(self, remote: SocketAddress, local: SocketAddress, sock: socket.socket):
        # override for user-customized channel
        channel = self._create_channel(remote=remote, local=local, sock=sock)
        assert channel is not None, 'failed to create socket channel: %s, remote=%s, local=%s' % (sock, remote, local)
        self._set_channel(channel=channel, remote=channel.remote_address, local=channel.local_address)


class ClientHub(StreamHub):
    """ Stream Client Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__lock = threading.Lock()

    # Override
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        conn = ActiveConnection(remote=remote, local=local)
        conn.delegate = self.delegate  # gate
        conn.start(hub=self)  # start FSM
        return conn

    # Override
    def open(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        assert remote is not None, 'remote address empty: %s, %s' % (remote, local)
        # try to get channel
        with self.__lock:
            old = self._get_channel(remote=remote, local=local)
            if old is None:
                # create channel with socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                channel = self._create_channel(sock, remote=remote, local=local)
                self._set_channel(channel, remote=remote, local=local)
            else:
                sock = None
                channel = old
        if old is None:
            # initialize socket
            sock = _init_socket(sock, remote=remote, local=local)
            if sock is None:
                print('[TCP] failed to prepare socket: %s -> %s' % (local, remote))
                self._remove_channel(channel, remote=remote, local=local)
        return channel


def _init_socket(sock: socket.socket, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[socket.socket]:
    try:
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
