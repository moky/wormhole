# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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
from typing import Optional

from .status import ConnectionStatus
from .base import BaseConnection


class ActiveConnection(BaseConnection):

    def __init__(self, address: tuple, sock: Optional[socket.socket] = None):
        super().__init__(sock=sock)
        assert isinstance(address, tuple), 'remote address error: %s' % str(address)
        self.__address = address
        self.__running = False
        # lock for connecting
        self.__lock = threading.RLock()
        self.__connecting = 0

    def __connect(self) -> bool:
        self.status = ConnectionStatus.Connecting
        try:
            sock = socket.socket()
            sock.connect(self.__address)
            self._sock = sock
            self.status = ConnectionStatus.Connected
            return True
        except socket.error as error:
            print('[TCP] failed to connect: %s, %s' % (self.__address, error))
            self.status = ConnectionStatus.Error
            return False

    def __reconnect(self) -> bool:
        with self.__lock:
            try:
                self.__connecting += 1
                if self.__connecting == 1 and self._sock is None:
                    redo = self.__connect()
                else:
                    redo = False
            finally:
                self.__connecting -= 1
            return redo

    @property
    def socket(self) -> Optional[socket.socket]:
        """ Get connected socket """
        if self.__running:
            if self._sock is None:
                self.__reconnect()
            return self._sock

    @property
    def address(self) -> Optional[tuple]:
        return self.__address

    @property
    def running(self) -> bool:
        return self.__running

    # Override
    def _receive(self) -> Optional[bytes]:
        data = super()._receive()
        if data is None and self.__reconnect():
            # try again
            data = super()._receive()
        return data

    # Override
    def send(self, data: bytes) -> int:
        res = super().send(data=data)
        if res < 0 and self.__reconnect():
            # try again
            res = super().send(data=data)
        return res

    # Override
    def stop(self):
        self.__running = False
        super().stop()

    # Override
    def setup(self):
        self.__running = True
        super().setup()

    # Override
    def finish(self):
        self.__running = False
        super().finish()
