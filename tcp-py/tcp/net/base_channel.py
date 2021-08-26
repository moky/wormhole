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
from abc import ABC, abstractmethod
from typing import Optional

from .channel import Channel


class BaseChannel(Channel, ABC):

    def __init__(self, sock: Optional[socket.socket] = None,
                 remote: Optional[tuple] = None, local: Optional[tuple] = None,
                 blocking: bool = True, reuse: bool = True):
        super().__init__()
        if sock is None:
            # BaseChannel(remote=remote, local=local, blocking=blocking, reuse=reuse),
            self._blocking = blocking
            self._reuse = reuse
            # setup inner socket
            self._sock = None
            sock = self._setup_socket()
            # bind to local address
            if local is not None:
                sock.bind(local)
            # connect to remote address
            if remote is not None:
                sock.connect(remote)
        else:
            # BaseChannel(sock=sock)
            self._blocking = sock.getblocking()
            self._reuse = getattr(sock, 'SO_REUSEPORT', 0)
            self._sock = sock

    @abstractmethod
    def _setup_socket(self) -> socket.socket:
        """ create socket (blocking, reuse) """
        raise NotImplemented

    # Override
    def configure_blocking(self, blocking: bool):
        self._blocking = blocking
        sock = self._sock
        if sock is None:
            sock = self._setup_socket()
        else:
            sock.setblocking(blocking)
        return sock

    @property  # Override
    def blocking(self) -> bool:
        sock = self._sock
        if sock is None:
            return self._blocking
        else:
            return sock.getblocking()

    @property  # Override
    def opened(self) -> bool:
        sock = self._sock
        return sock is not None and not getattr(sock, '_closed', False)

    @property  # Override
    def connected(self) -> bool:
        try:
            return self.remote_address is not None
        except socket.error:
            return False

    @property  # Override
    def bound(self) -> bool:
        try:
            return self.local_address is not None
        except socket.error:
            return False

    @property  # Override
    def local_address(self) -> Optional[tuple]:
        sock = self._sock
        if sock is None:
            return None
        else:
            # assert isinstance(sock, socket.socket)
            return sock.getsockname()

    @property  # Override
    def remote_address(self) -> Optional[tuple]:
        sock = self._sock
        if sock is None:
            return None
        try:
            # assert isinstance(sock, socket.socket)
            return sock.getpeername()
        except socket.error as error:
            if error.strerror == 'Socket is not connected':
                return None
            else:
                raise error

    # Override
    def bind(self, address: Optional[tuple] = None, host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self._setup_socket()
        # assert isinstance(sock, socket.socket)
        sock.bind(address)

    # Override
    def connect(self, address: Optional[tuple] = None, host: Optional[str] = '127.0.0.1', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self._setup_socket()
        # assert isinstance(sock, socket.socket)
        sock.connect(address)

    # Override
    def disconnect(self):
        sock = self._sock
        self.close()
        return sock

    # Override
    def close(self):
        sock = self._sock
        if sock is not None and not getattr(sock, '_closed', False):
            # sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        self._sock = None

    #
    #   Input/Output
    #

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        # check socket
        sock = self._sock
        if sock is None:
            raise socket.error('socket lost, cannot read data')
        # try to receive data
        try:
            data = sock.recv(max_len)
        except socket.error as error:
            # the socket will raise 'Resource temporarily unavailable'
            # when received nothing in non-blocking mode,
            # here we should ignore this exception.
            if not self._blocking:
                if error.strerror == 'Resource temporarily unavailable':
                    # received nothing
                    return None
            raise error
        # check data
        if data is None or len(data) == 0:
            # in blocking mode, the socket will wait until received something,
            # but if timeout was set, it will return None too, it's normal;
            # otherwise, we know the connection was lost.
            if sock.gettimeout() is None:  # and self._blocking
                raise socket.error('remote peer reset socket')
        return data

    # Override
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
