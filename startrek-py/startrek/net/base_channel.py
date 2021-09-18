# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
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
from typing import Optional

from .channel import Channel


class BaseChannel(Channel, ABC):

    def __init__(self, sock: socket.socket, remote: Optional[tuple], local: Optional[tuple]):
        super().__init__()
        self.__sock = sock
        self.__remote = remote
        self.__local = local

    @property  # protected
    def sock(self) -> Optional[socket.socket]:
        return self.__sock

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (clazz, self.__remote, self.__local)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (clazz, self.__remote, self.__local)

    # Override
    def configure_blocking(self, blocking: bool):
        sock = self.sock
        if sock is None:
            raise socket.error('socket closed')
        else:
            sock.setblocking(blocking)
        return sock

    @property  # Override
    def blocking(self) -> bool:
        sock = self.sock
        return sock is not None and sock.getblocking()

    @property  # Override
    def opened(self) -> bool:
        sock = self.sock
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
        return self.__local

    @property  # Override
    def remote_address(self) -> Optional[tuple]:
        return self.__remote

    # Override
    def bind(self, address: Optional[tuple] = None, host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.sock
        if sock is None:
            raise socket.error('socket closed')
        sock.bind(address)
        self.__local = address
        return sock

    # Override
    def connect(self, address: Optional[tuple] = None, host: Optional[str] = '127.0.0.1', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.sock
        if sock is None:
            raise socket.error('socket closed')
        sock.connect(address)
        self.__remote = address
        return sock

    # Override
    def disconnect(self):
        sock = self.sock
        self.close()
        return sock

    # Override
    def close(self):
        sock = self.sock
        if sock is not None and not getattr(sock, '_closed', False):
            # sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        self.__sock = None

    #
    #   Input/Output
    #

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        # check socket
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot read data')
        # try to receive data
        try:
            data = sock.recv(max_len)
        except socket.error as error:
            # the socket will raise 'Resource temporarily unavailable'
            # when received nothing in non-blocking mode,
            # here we should ignore this exception.
            if not self.blocking:
                if error.strerror == 'Resource temporarily unavailable':
                    # received nothing
                    return None
            raise error
        # check data
        if data is None or len(data) == 0:
            # in blocking mode, the socket will wait until received something,
            # but if timeout was set, it will return None too, it's normal;
            # otherwise, we know the connection was lost.
            if sock.gettimeout() is None:  # and self.blocking:
                raise socket.error('remote peer reset socket')
        return data

    # Override
    def write(self, data: bytes) -> int:
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot write data: %d byte(s)' % len(data))
        # return sock.sendall(data)
        return sendall(data=data, sock=sock)


def sendall(data: bytes, sock: socket.socket) -> int:
    sent = 0
    rest = len(data)
    while rest > 0:  # and not getattr(sock, '_closed', False):
        cnt = sock.send(data)
        if cnt > 0:
            sent += cnt
            rest -= cnt
            data = data[cnt:]
    return sent
