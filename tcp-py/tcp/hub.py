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
from typing import Optional, Set, Dict

from startrek.fsm import Runnable
from startrek import Channel
from startrek import Connection, ConnectionDelegate
from startrek import BaseConnection, ActiveConnection
from startrek import BaseHub

from .channel import StreamChannel


class StreamHub(BaseHub, ABC):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        # remote => channel
        self.__channels: Dict[tuple, Channel] = {}

    def put_channel(self, channel: Channel):
        remote = channel.remote_address
        self.__channels[remote] = channel

    # Override
    def _all_channels(self) -> Set[Channel]:
        return set(self.__channels.values())

    # Override
    def open_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Channel]:
        assert remote is not None, 'remote address empty'
        return self.__channels.get(remote)

    # Override
    def close_channel(self, channel: Channel):
        if channel is None:
            return False
        else:
            self.__remove_channel(channel=channel)
        try:
            if channel.opened:
                channel.close()
            return True
        except socket.error:
            return False

    def __remove_channel(self, channel: Channel):
        remote = channel.remote_address
        if self.__channels.pop(remote, None) == channel:
            # removed by key
            return True
        # remove by value
        for key in self.__channels:
            if self.__channels.get(key) == channel:
                self.__channels.pop(key, None)
                return True


class ServerHub(StreamHub, Runnable):
    """ Stream Server Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__local_address: Optional[tuple] = None
        self.__master: Optional[socket.socket] = None
        # running thread
        self.__thread: Optional[Thread] = None
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    # Override
    def _create_connection(self, sock: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        gate = self.delegate
        conn = BaseConnection(remote=remote, local=None, channel=sock, delegate=gate, hub=self)
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
        t = Thread(target=self.run)
        self.__thread = t
        t.start()

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
                if sock is not None:
                    channel = StreamChannel(sock=sock, remote=address, local=self.__local_address)
                    self.put_channel(channel=channel)
            except socket.error as error:
                print('[TCP] accepting connection error: %s' % error)


class ClientHub(StreamHub):
    """ Stream Client Hub """

    # Override
    def _create_connection(self, sock: Channel, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        gate = self.delegate
        conn = ActiveConnection(remote=remote, local=None, channel=sock, delegate=gate, hub=self)
        conn.start()  # start FSM
        return conn

    # Override
    def open_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Channel]:
        channel = super().open_channel(remote=remote, local=local)
        if channel is None:  # and remote is not None:
            channel = create_channel(remote=remote, local=local)
            if channel is not None:
                self.put_channel(channel=channel)
        return channel


def create_channel(remote: tuple, local: Optional[tuple]) -> Optional[Channel]:
    try:
        sock = create_socket(remote=remote, local=local)
        if local is None:
            local = sock.getsockname()
        return StreamChannel(sock=sock, remote=remote, local=local)
    except socket.error as error:
        print('[TCP] creating connection error: %s' % error)


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
