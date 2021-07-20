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
from typing import Optional

from .net import Channel


class StreamChannel(Channel):

    def __init__(self, sock: Optional[socket.socket] = None,
                 remote: Optional[tuple] = None, local: Optional[tuple] = None, blocking: bool = True):
        super().__init__()
        if sock is None:
            self.__blocking = blocking
            # create inner socket
            sock = socket.socket()
            sock.setblocking(blocking)
            # bind to local address
            if local is not None:
                sock.bind(local)
            # connect to remote address
            if remote is not None:
                sock.connect(remote)
        self._sock = sock
        if sock is None:
            self.__blocking = True
            # self.__reuse_port = 0
        else:
            self.__blocking = sock.getblocking()
            # self.__reuse_port = getattr(sock, 'SO_REUSEPORT', 0)

    def __set_impl(self):
        if self._sock is None:
            self._sock = socket.socket()
            self._sock.setblocking(self.__blocking)
            # self._sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, self.__reuse_port)

    def configure_blocking(self, blocking: bool):
        self.__blocking = blocking
        sock = self._sock
        if sock is None:
            self.__set_impl()
        else:
            sock.setblocking(blocking)

    @property
    def blocking(self) -> bool:
        sock = self._sock
        if sock is None:
            return self.__blocking
        else:
            return sock.getblocking()

    @property
    def opened(self) -> bool:
        sock = self._sock
        return sock is not None and not getattr(sock, '_closed', False)

    @property
    def connected(self) -> bool:
        sock = self._sock
        return sock is not None

    @property
    def bound(self) -> bool:
        sock = self._sock
        try:
            return sock is not None and sock.getsockname() is not None
        except socket.error:
            return False

    @property
    def local_address(self) -> Optional[tuple]:
        sock = self._sock
        if sock is not None:
            # assert isinstance(sock, socket.socket)
            return sock.getsockname()

    @property
    def remote_address(self) -> Optional[tuple]:
        sock = self._sock
        if sock is not None:
            # assert isinstance(sock, socket.socket)
            return sock.getpeername()

    def bind(self, host: str, port: int):
        self.__set_impl()
        sock = self._sock
        # assert isinstance(sock, socket.socket)
        address = (host, port)
        sock.bind(address)

    def connect(self, host: str, port: int):
        self.__set_impl()
        sock = self._sock
        # assert isinstance(sock, socket.socket)
        address = (host, port)
        sock.connect(address)

    def disconnect(self):
        self.close()

    def close(self):
        sock = self._sock
        if sock is not None and not getattr(sock, '_closed', False):
            # sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        self._sock = None

    #
    #   Input/Output
    #

    def read(self, max_len: int) -> bytes:
        sock = self._sock
        if sock is None:
            raise socket.error('socket lost, cannot read data')
        data = sock.recv(max_len)
        if data is None or len(data) == 0:
            if sock.gettimeout() is None:
                raise socket.error('remote peer reset socket')
        return data

    def write(self, data: bytes) -> int:
        sock = self._sock
        if sock is None:
            raise socket.error('socket lost, cannot write data: %d byte(s)' % len(data))
        # sock.sendall(data)
        sent = 0
        rest = len(data)
        while rest > 0:  # and not getattr(sock, '_closed', False):
            cnt = sock.send(data)
            if cnt > 0:
                sent += cnt
                rest -= cnt
                data = data[cnt:]
        return sent

    def receive(self, max_len: int) -> (bytes, tuple):
        data = self.read(max_len=max_len)
        if data is None or len(data) == 0:
            return None, None
        else:
            return data, self.remote_address

    def send(self, data: bytes, target: tuple) -> int:
        # TCP channel will be always connected
        # so the target address must be the remote address
        return self.write(data=data)
