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
from typing import Optional

from tcp import Channel


class DiscreteChannel(Channel):

    def __init__(self, sock: Optional[socket.socket] = None,
                 remote: Optional[tuple] = None, local: Optional[tuple] = None,
                 blocking: bool = True, reuse: bool = True):
        super().__init__()
        if sock is None:
            # DiscreteChannel(remote=remote, local=local, blocking=blocking, reuse=reuse),
            self.__blocking = blocking
            self.__reuse = reuse
            self._sock = None
            # setup inner socket
            sock = self._setup()
            # bind to local address
            if local is not None:
                sock.bind(local)
            # connect to remote address
            if remote is not None:
                sock.connect(remote)
        else:
            # DiscreteChannel(sock=sock)
            self.__blocking = sock.getblocking()
            self.__reuse = getattr(sock, 'SO_REUSEPORT', 0)
            self._sock = sock

    def _setup(self) -> socket.socket:
        sock = self._sock
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, self.__reuse)
            sock.setblocking(self.__blocking)
            self._sock = sock
        return sock

    def configure_blocking(self, blocking: bool):
        self.__blocking = blocking
        sock = self._sock
        if sock is None:
            self._setup()
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
        sock = self._setup()
        # assert isinstance(sock, socket.socket)
        address = (host, port)
        sock.bind(address)

    def connect(self, host: str, port: int):
        sock = self._setup()
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
        sock = self._sock
        if sock is None:
            raise socket.error('socket lost, cannot receive data')
        data, remote = sock.recvfrom(max_len)
        if data is None or len(data) == 0:
            if sock.gettimeout() is None:
                raise socket.error('remote peer reset socket')
        return data, remote

    def send(self, data: bytes, target: tuple) -> int:
        sock = self._sock
        if sock is None:
            raise socket.error('socket lost, cannot send data: %d byte(s)' % len(data))
        # sock.sendall(data)
        return sock.sendto(data, target)
