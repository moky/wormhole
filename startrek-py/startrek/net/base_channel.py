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
from abc import ABC, abstractmethod
from typing import Optional

from ..types import AddressPairObject

from .channel import get_local_address, get_remote_address
from .channel import is_blocking, is_closed
from .channel import Channel


class Reader(ABC):
    """ socket reader """

    @abstractmethod
    def read(self, max_len: int) -> Optional[bytes]:
        """ read data from socket """
        raise NotImplemented

    @abstractmethod
    def receive(self, max_len: int) -> (Optional[bytes], Optional[tuple]):
        """ receive data via socket, and return it with remote address """
        raise NotImplemented


class Writer(ABC):
    """ socket writer """

    @abstractmethod
    def write(self, data: bytes) -> int:
        """ write data into socket """
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: tuple) -> int:
        """ send data via socket with remote address """
        raise NotImplemented


class BaseChannel(AddressPairObject, Channel, ABC):

    def __init__(self, remote: Optional[tuple], local: Optional[tuple], sock: socket.socket):
        super().__init__(remote=remote, local=local)
        self.__sock = sock
        self.__reader = self._create_reader()
        self.__writer = self._create_writer()
        # flags
        self.__blocking = False
        self.__opened = False
        self.__connected = False
        self.__bound = False
        self._refresh_flags()

    @property  # protected
    def reader(self) -> Reader:
        return self.__reader

    @property  # protected
    def writer(self) -> Writer:
        return self.__writer

    @abstractmethod
    def _create_reader(self) -> Reader:
        raise NotImplemented

    @abstractmethod
    def _create_writer(self) -> Writer:
        raise NotImplemented

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

    @property
    def sock(self) -> Optional[socket.socket]:
        return self.__sock

    # Override
    def configure_blocking(self, blocking: bool):
        sock = self.sock
        if sock is None:
            raise socket.error('socket closed: remote=%s, local=%s' % (self.remote_address, self.local_address))
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
            raise socket.error('cannot bind socket: local=(%s:%d)' % address)
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
            raise socket.error('cannot connect socket: remote=(%s:%d)' % address)
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

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        return self.reader.read(max_len=max_len)

    # Override
    def write(self, data: bytes) -> int:
        return self.writer.write(data=data)

    # Override
    def receive(self, max_len: int) -> (Optional[bytes], Optional[tuple]):
        return self.receive(max_len=max_len)

    # Override
    def send(self, data: bytes, target: tuple) -> int:
        return self.writer.send(data=data, target=target)
