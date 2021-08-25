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
                 remote: Optional[tuple] = None, local: Optional[tuple] = None,
                 blocking: bool = True, reuse: bool = True):
        super().__init__()
        if sock is None:
            # StreamChannel(remote=remote, local=local, blocking=blocking, reuse=reuse),
            self.__blocking = blocking
            self.__reuse = reuse
            # setup inner socket
            self._sock = None
            sock = self.__setup()
            # bind to local address
            if local is not None:
                sock.bind(local)
            # connect to remote address
            if remote is not None:
                sock.connect(remote)
        else:
            # StreamChannel(sock=sock)
            self.__blocking = sock.getblocking()
            self.__reuse = getattr(sock, 'SO_REUSEPORT', 0)
            self._sock = sock

    def __setup(self) -> socket.socket:
        sock = self._sock
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, self.__reuse)
            sock.setblocking(self.__blocking)
            self._sock = sock
        return sock

    def configure_blocking(self, blocking: bool):
        self.__blocking = blocking
        sock = self._sock
        if sock is None:
            self.__setup()
        else:
            sock.setblocking(blocking)
        return sock

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
        try:
            return self.remote_address is not None
        except socket.error:
            return False

    @property
    def bound(self) -> bool:
        try:
            return self.local_address is not None
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

    def bind(self, address: Optional[tuple] = None, host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.__setup()
        # assert isinstance(sock, socket.socket)
        sock.bind(address)

    def connect(self, address: Optional[tuple] = None, host: Optional[str] = '127.0.0.1', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.__setup()
        # assert isinstance(sock, socket.socket)
        sock.connect(address)

    def disconnect(self):
        sock = self._sock
        self.close()
        return sock

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
        try:
            data = self.read(max_len=max_len)
        except socket.error as error:
            if not self.__blocking:
                if error.strerror == 'Resource temporarily unavailable':
                    # received nothing
                    return None, None
            raise error
        if data is None or len(data) == 0:
            return None, None
        else:
            return data, self.remote_address

    def send(self, data: bytes, target: tuple) -> int:
        # TCP channel will be always connected
        # so the target address must be the remote address
        return self.write(data=data)
