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
from abc import ABC
from typing import Optional, Iterable

from startrek.types import SocketAddress, AddressPairMap
from startrek.fsm import Runnable, Daemon
from startrek.net.channel import close_socket
from startrek import Channel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import StreamChannel
from .channel import create_socket


class ChannelPool(AddressPairMap[Channel]):

    # Override
    def set(self, item: Optional[Channel], remote: Optional[SocketAddress], local: Optional[SocketAddress]):
        old = self.get(remote=remote, local=local)
        if old is not None and old is not item:
            self.remove(item=old, remote=remote, local=local)
        super().set(item=item, remote=remote, local=local)

    # Override
    def remove(self, item: Optional[Channel],
               remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        cached = super().remove(item=item, remote=remote, local=local)
        if cached is not None:
            if not cached.closed:
                cached.close()
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
    def _create_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress],
                        sock: socket.socket) -> Channel:
        """ create channel with socket & addresses """
        return StreamChannel(remote=remote, local=local, sock=sock)

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

    def _set_channel(self, channel: Channel, remote: Optional[SocketAddress], local: Optional[SocketAddress]):
        """ cache channel """
        self.__channel_pool.set(item=channel, remote=remote, local=local)

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
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress],
                           channel: Optional[Channel]) -> Optional[Connection]:
        assert channel is not None, 'server channel should not be empty: %s -> %s' % (remote, local)
        conn = BaseConnection(remote=remote, local=local, channel=channel)
        conn.delegate = self.delegate  # gate
        conn.start()  # start FSM
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
            close_socket(sock=old)

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
    def _create_connection(self, remote: SocketAddress, local: Optional[SocketAddress],
                           channel: Optional[Channel]) -> Optional[Connection]:
        conn = ActiveConnection(remote=remote, local=local, channel=channel, hub=self)
        conn.delegate = self.delegate  # gate
        conn.start()  # start FSM
        return conn

    # Override
    def open(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        channel = super().open(remote=remote, local=local)
        if channel is not None:
            # channel already exists
            return channel
        assert remote is not None, 'remote address should not be empty'
        with self.__lock:
            channel = self._get_channel(remote=remote, local=local)
            if channel is not None:
                # channel was created just now
                return channel
            # get from socket pool
            sock = create_socket(remote=remote, local=local)
            if sock is None:
                # failed to connect remote address
                return None
            # elif local is None:
            #     local = get_local_address(sock=sock)
            # create channel with socket
            channel = self._create_channel(remote=remote, local=local, sock=sock)
            if channel is not None:
                self._set_channel(channel=channel, remote=channel.remote_address, local=channel.local_address)
                return channel
