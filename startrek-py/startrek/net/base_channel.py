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

from ..types import AddressPairObject
from .channel import Channel
from .channel import get_local_address, get_remote_address, is_blocking, is_closed


class BaseChannel(AddressPairObject, Channel, ABC):

    def __init__(self, remote: Optional[tuple], local: Optional[tuple], sock: socket.socket):
        super().__init__(remote=remote, local=local)
        self.__sock = sock
        # flags
        self.__blocking = False
        self.__opened = False
        self.__connected = False
        self.__bound = False
        self._refresh_flags()

    def _refresh_flags(self):
        sock = self.sock
        if sock is None:
            self.__blocking = False
            self.__opened = False
            self.__connected = False
            self.__bound = False
        else:
            self.__blocking = is_blocking(sock=sock)
            self.__opened = not is_closed(sock=sock)
            self.__connected = get_remote_address(sock=sock) is not None
            self.__bound = get_local_address(sock=sock) is not None

    @property  # protected
    def sock(self) -> Optional[socket.socket]:
        return self.__sock

    # Override
    def configure_blocking(self, blocking: bool):
        sock = self.sock
        if sock is None:
            raise socket.error('socket closed')
        else:
            sock.setblocking(blocking)
        self.__blocking = blocking
        return sock

    @property  # Override
    def blocking(self) -> bool:
        return self.__blocking

    @property  # Override
    def opened(self) -> bool:
        return self.__opened

    @property  # Override
    def connected(self) -> bool:
        return self.__connected

    @property  # Override
    def bound(self) -> bool:
        return self.__bound

    @property  # Override
    def alive(self) -> bool:
        return self.opened and (self.connected or self.bound)

    # Override
    def bind(self, address: Optional[tuple] = None, host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.sock
        if sock is None:
            raise socket.error('socket closed')
        sock.bind(address)
        self._local = address
        self.__bound = True
        self.__opened = True
        self.__blocking = is_blocking(sock=sock)
        return sock

    # Override
    def connect(self, address: Optional[tuple] = None, host: Optional[str] = '127.0.0.1', port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.sock
        if sock is None:
            raise socket.error('socket closed')
        sock.connect(address)
        self._remote = address
        self.__connected = True
        self.__opened = True
        self.__blocking = is_blocking(sock=sock)
        return sock

    # Override
    def disconnect(self) -> Optional[socket.socket]:
        sock = self.__sock
        self.close()
        return sock

    # Override
    def close(self):
        sock = self.__sock
        if sock is not None and not is_closed(sock=sock):
            # sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        self.__sock = None
        # update flags
        self.__blocking = False
        self.__opened = False
        self.__connected = False
        self.__bound = False

    #
    #   Input/Output
    #

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        # check socket first
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot read data')
        # try to receive data
        try:
            data = sock.recv(max_len)
        except socket.error as error:
            error = self._check_socket_error(error=error)
            if error is not None:
                # connection lost?
                raise error
            # received nothing
            return None
        # check data
        error = self._check_received_data(data=data)
        if error is not None:
            # connection lost!
            raise error
        # OK
        return data

    # Override
    def write(self, data: bytes) -> int:
        # check socket first
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot write data: %d byte(s)' % len(data))
        # try to send data
        sent = 0
        try:
            # sent = sock.sendall(data)
            rest = len(data)
            while rest > 0:  # and not is_closed(sock=sock):
                cnt = sock.send(data)
                if cnt > 0:
                    sent += cnt
                    rest -= cnt
                    data = data[cnt:]
        except socket.error as error:
            error = self._check_socket_error(error=error)
            if error is not None:
                # connection lost?
                raise error
            # buffer overflow!
            if sent == 0:
                return -1
        return sent

    #
    #   Check for socket errors
    #
    ResourceTemporarilyUnavailable = 'Resource temporarily unavailable'

    def _check_socket_error(self, error: socket.error) -> Optional[socket.error]:
        # the socket will raise 'Resource temporarily unavailable'
        # when received nothing in non-blocking mode,
        # or buffer overflow while sending too many bytes,
        # here we should ignore this exception.
        if not self.blocking:
            if error.strerror == self.ResourceTemporarilyUnavailable:
                return None
        # print('[NET] socket error: %s' % error)
        return error

    def _check_received_data(self, data: Optional[bytes]) -> Optional[socket.error]:
        # in blocking mode, the socket will wait until received something,
        # but if timeout was set, it will return None too, it's normal;
        # otherwise, we know the connection was lost.
        if data is None or len(data) == 0:
            if self.sock.gettimeout() is None:  # and self.blocking:
                # print('[NET] socket error: remote peer reset socket')
                return socket.error('remote peer reset socket')
