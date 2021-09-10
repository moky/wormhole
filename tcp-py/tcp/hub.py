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
import weakref
from typing import Optional

from startrek.fsm import Runnable
from startrek import Channel, Connection, ConnectionDelegate
from startrek import BaseHub, BaseConnection, ActiveConnection

from .channel import StreamChannel


class ServerHub(BaseHub, Runnable):
    """ Stream Server Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__slaves = weakref.WeakValueDictionary()  # address -> socket
        self.__local_address: Optional[tuple] = None
        self.__master: Optional[socket.socket] = None
        self.__running = False

    def bind(self, address: Optional[tuple] = None, host: Optional[str] = None, port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.__master
        if sock is not None:
            if not getattr(sock, '_closed', False):
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
        threading.Thread(target=self.run).start()

    def stop(self):
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    def run(self):
        self.__running = True
        while self.running:
            try:
                sock, address = self.__master.accept()
                if sock is not None:
                    self.__slaves[address] = sock
                    self.connect(remote=address, local=self.__local_address)
            except socket.error as error:
                print('[NET] accept connection error: %s' % error)

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with channel
        sock = self.create_channel(remote=remote, local=local)
        conn = BaseConnection(remote=remote, local=local, channel=sock)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn

    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__slaves.get(remote)
        if sock is not None:
            return StreamChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class ClientHub(BaseHub):
    """ Stream Client Hub """

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with addresses
        conn = ActiveStreamConnection(remote=remote, local=local)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn


class ActiveStreamConnection(ActiveConnection):
    """ Active Stream Connection """

    # Override
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        channel = StreamChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel
