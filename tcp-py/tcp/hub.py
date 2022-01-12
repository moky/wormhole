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
from threading import Thread
from typing import Optional, Set

from startrek.fsm import Runnable
from startrek.types import AddressPairMap
from startrek.net.channel import get_local_address
from startrek import Channel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import StreamChannel


class StreamHub(BaseHub, ABC):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__channel_pool: AddressPairMap[Channel] = AddressPairMap()

    def put_channel(self, channel: Channel):
        self._set_channel(channel=channel)

    # Override
    def _all_channels(self) -> Set[Channel]:
        return self.__channel_pool.items

    def _get_channel(self, remote: Optional[tuple]) -> Optional[Channel]:
        return self.__channel_pool.get(remote=remote, local=None)

    def _set_channel(self, channel: Channel):
        remote = channel.remote_address
        # check old channel
        old = self.__channel_pool.get(remote=remote, local=None)
        if old is not None and old is not channel:
            self._close_channel(channel=old)
        # set new channel
        self.__channel_pool.set(remote=remote, local=None, item=channel)

    # Override
    def _remove_channel(self, channel: Channel):
        remote = channel.remote_address
        old = self.__channel_pool.remove(remote=remote, local=None, item=channel)
        if old is not None and old is not channel:
            # should not happen
            self._close_channel(channel=old)

    # noinspection PyMethodMayBeStatic
    def _close_channel(self, channel: Channel):
        if channel.opened:
            channel.close()

    # Override
    def open(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Channel]:
        assert remote is not None, 'remote address empty: %s, %s' % (remote, local)
        return self._get_channel(remote=remote)


class ServerHub(StreamHub, Runnable):
    """ Stream Server Hub """

    def __init__(self, delegate: ConnectionDelegate, daemon: bool = False):
        super().__init__(delegate=delegate)
        self.__local_address: Optional[tuple] = None
        self.__master: Optional[socket.socket] = None
        # running thread
        self.__thread: Optional[Thread] = None
        self.__running = False
        self.__daemon = daemon

    @property
    def running(self) -> bool:
        return self.__running

    # Override
    def _create_connection(self, channel: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        gate = self.delegate
        conn = BaseConnection(remote=remote, local=None, channel=channel, delegate=gate, hub=self)
        conn.start()  # start FSM
        return conn

    def bind(self, address: Optional[tuple] = None, host: Optional[str] = None, port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.__master
        if sock is not None and not getattr(sock, '_closed', False):
            sock.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(True)
        sock.bind(address)
        sock.listen(1)
        # sock.setblocking(False)
        self.__master = sock
        self.__local_address = address

    def start(self):
        self.__force_stop()
        self.__running = True
        thr = Thread(target=self.run, daemon=self.__daemon)
        self.__thread = thr
        thr.start()
        return thr

    def __force_stop(self):
        self.__running = False
        t: Thread = self.__thread
        if t is not None:
            # waiting 2 seconds for stopping the thread
            self.__thread = None
            t.join(timeout=2.0)

    def stop(self):
        self.__force_stop()

    # Override
    def run(self):
        self.__running = True
        while self.running:
            try:
                sock, address = self.__master.accept()
                self._accept(sock=sock, remote=address, local=self.__local_address)
            except socket.error as error:
                print('[TCP] socket error: %s' % error)
            except Exception as error:
                print('[TCP] accept error: %s' % error)

    def _accept(self, sock: socket.socket, remote: tuple, local: tuple):
        # override for user-customized channel
        assert sock is not None, 'socket error: %s, %s' % (remote, local)
        channel = StreamChannel(sock=sock, remote=remote, local=local)
        self._set_channel(channel=channel)


class ClientHub(StreamHub):
    """ Stream Client Hub """

    # Override
    def _create_connection(self, channel: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        gate = self.delegate
        conn = ActiveConnection(remote=remote, local=None, channel=channel, delegate=gate, hub=self)
        conn.start()  # start FSM
        return conn

    # Override
    def open(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Channel]:
        channel = super().open(remote=remote, local=local)
        if channel is None:  # and remote is not None:
            channel = self._create_channel(remote=remote, local=local)
            if channel is not None:
                self._set_channel(channel=channel)
        return channel

    # noinspection PyMethodMayBeStatic
    def _create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Channel]:
        # override for user-customized channel
        try:
            sock = create_socket(remote=remote, local=local)
        except socket.error as error:
            print('[TCP] creating connection %s -> %s error: %s' % (local, remote, error))
            return None
        if local is None:
            local = get_local_address(sock=sock)
        return StreamChannel(remote=remote, local=local, sock=sock)


def create_socket(remote: tuple, local: Optional[tuple]) -> Optional[socket.socket]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
    sock.setblocking(True)
    if local is not None:
        sock.bind(local)
    # assert remote is not None
    sock.connect(remote)
    sock.setblocking(False)
    return sock
