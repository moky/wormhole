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
from abc import ABC
from typing import Optional, Iterable

from startrek.types import Address, AddressPairMap
from startrek.fsm import Runnable, Daemon
from startrek.net.channel import is_opened, get_local_address
from startrek import Channel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import StreamChannel


class ChannelPool(AddressPairMap[Channel]):

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
            if cached.opened:
                cached.close()
            return cached


class StreamHub(BaseHub, ABC):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__channel_pool = ChannelPool()

    #
    #   Channel
    #

    # noinspection PyMethodMayBeStatic
    def _create_channel(self, sock: socket.socket, remote: Optional[Address], local: Optional[Address]) -> Channel:
        """ create channel with socket & addresses """
        return StreamChannel(remote=remote, local=local, sock=sock)

    # Override
    def _all_channels(self) -> Iterable[Channel]:
        """ get a copy of all channels """
        return self.__channel_pool.items

    # Override
    def _remove_channel(self, channel: Channel):
        """ remove cached channel """
        self.__channel_pool.remove(remote=channel.remote_address, local=channel.local_address, item=channel)

    def _get_channel(self, remote: Optional[Address], local: Optional[Address]) -> Optional[Channel]:
        """ get cached channel """
        return self.__channel_pool.get(remote=remote, local=local)

    def _set_channel(self, channel: Channel):
        """ cache channel """
        self.__channel_pool.set(remote=channel.remote_address, local=channel.local_address, item=channel)

    # Override
    def open(self, remote: Optional[Address], local: Optional[Address]) -> Optional[Channel]:
        assert remote is not None, 'remote address empty: %s, %s' % (remote, local)
        return self.__channel_pool.get(remote=remote, local=None)


class ServerHub(StreamHub, Runnable):
    """ Stream Server Hub """

    def __init__(self, delegate: ConnectionDelegate, daemonic: bool = True):
        super().__init__(delegate=delegate)
        self.__local = None   # Address
        self.__master = None  # socket.socket
        # running thread
        self.__daemon = Daemon(target=self.run, daemonic=daemonic)
        self.__running = False

    def _get_master(self) -> Optional[socket.socket]:
        return self.__master

    def _set_master(self, master: socket.socket):
        # 1. check old socket
        old = self._get_master()
        if old is not None and old is not master:
            if is_opened(sock=old):
                old.close()
        # 2. set new socket
        self.__master = master

    @property
    def local_address(self) -> Optional[Address]:
        return self.__local

    @local_address.setter
    def local_address(self, address: Address):
        self.__local = address

    @property
    def running(self) -> bool:
        return self.__running

    # Override
    def _create_connection(self, channel: Channel, remote: Address, local: Optional[Address]) -> Optional[Connection]:
        gate = self.delegate
        conn = BaseConnection(remote=remote, local=None, channel=channel, delegate=gate)
        conn.start()  # start FSM
        return conn

    def bind(self, address: Optional[Address] = None, host: Optional[str] = None, port: Optional[int] = 0):
        if address is None:
            if port > 0:
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
                self._accept(sock=sock, remote=address, local=self.local_address)
            except socket.error as error:
                print('[TCP] socket error: %s' % error)
            except Exception as error:
                print('[TCP] accept error: %s' % error)

    def _accept(self, sock: socket.socket, remote: Address, local: Address):
        # override for user-customized channel
        assert sock is not None, 'socket error: %s, %s' % (remote, local)
        channel = self._create_channel(sock=sock, remote=remote, local=local)
        assert channel is not None, 'failed to create socket channel: %s, remote=%s, local=%s' % (sock, remote, local)
        self._set_channel(channel=channel)


class ClientHub(StreamHub):
    """ Stream Client Hub """

    # Override
    def _create_connection(self, channel: Channel, remote: Address, local: Optional[Address]) -> Optional[Connection]:
        gate = self.delegate
        conn = ActiveConnection(remote=remote, local=None, channel=channel, delegate=gate, hub=self)
        conn.start()  # start FSM
        return conn

    # Override
    def open(self, remote: Optional[Address], local: Optional[Address]) -> Optional[Channel]:
        channel = super().open(remote=remote, local=local)
        if channel is None:  # and remote is not None:
            channel = self.__create_socket_channel(remote=remote, local=local)
            if channel is not None:
                self._set_channel(channel=channel)
        return channel

    def __create_socket_channel(self, remote: Optional[Address], local: Optional[Address]) -> Optional[Channel]:
        # override for user-customized channel
        try:
            sock = create_socket(remote=remote, local=local)
            if local is None:
                local = get_local_address(sock=sock)
            return self._create_channel(sock=sock, remote=remote, local=local)
        except socket.error as error:
            print('[TCP] failed to create channel %s -> %s: %s' % (local, remote, error))


def create_socket(remote: Address, local: Optional[Address]) -> Optional[socket.socket]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
    sock.setblocking(True)
    if local is not None:
        sock.bind(local)
    # assert remote is not None
    sock.connect(remote)
    sock.setblocking(False)
    return sock
