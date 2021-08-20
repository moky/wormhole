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
import threading
from abc import abstractmethod
from typing import Optional

from tcp import Channel, ConnectionState, ConnectionStateMachine

from ..mtp import DataType, Package

from .pack_conn import PING
from .pack_conn import PackageConnection


class ActivePackageConnection(PackageConnection):

    def __init__(self, remote: tuple, local: Optional[tuple] = None, channel: Optional[Channel] = None):
        super().__init__(remote=remote, local=local, channel=channel)
        self.__lock = threading.RLock()
        self.__connecting = 0
        self.__running = False

    @abstractmethod
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        raise NotImplemented

    def __reconnect(self):
        redo = False
        with self.__lock:
            try:
                self.__connecting += 1
                if self.__connecting == 1 and self.__running:
                    self.change_state(name=ConnectionState.CONNECTING)
                    self._channel = self.connect(remote=self._remote_address, local=self._local_address)
                    if self._channel is None:
                        self.change_state(name=ConnectionState.ERROR)
                    else:
                        self.change_state(name=ConnectionState.CONNECTED)
                        redo = True
            finally:
                self.__connecting -= 1
        return redo

    @property
    def channel(self) -> Channel:
        if self._channel is None:
            self.__reconnect()
        return self._channel

    @property
    def opened(self) -> bool:
        return self.__running

    def start(self):
        self.__running = True
        super().start()

    def stop(self):
        self.__running = False
        super().stop()

    def _receive(self, max_len: int) -> (bytes, tuple):
        data, remote = super()._receive(max_len=max_len)
        if data is None and remote is None and self._channel is None and self.__reconnect():
            # try again
            data, remote = super()._receive(max_len=max_len)
        return data, remote

    def send(self, data: bytes, target: Optional[tuple] = None) -> int:
        sent = super().send(data=data, target=target)
        if sent == -1 and self._channel is None and self.__reconnect():
            # try again
            sent = super().send(data=data, target=target)
        return sent

    def enter_state(self, state: ConnectionState, ctx: ConnectionStateMachine):
        super().enter_state(state=state, ctx=ctx)
        if state == ConnectionState.EXPIRED:
            try:
                self.heartbeat()
            except socket.error as error:
                print('[NET] failed to heartbeat: %s' % error)

    def heartbeat(self):
        """ Send a heartbeat package to remote address """
        pack = Package.new(data_type=DataType.COMMAND, body=PING)
        self.send(data=pack.get_bytes(), target=self.remote_address)
