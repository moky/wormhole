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

from ..types import Address, AddressPairObject

from .channel import is_blocking, is_opened, is_connected, is_bound
from .channel import Channel


class Reader(ABC):
    """ socket reader """

    @abstractmethod
    def read(self, max_len: int) -> Optional[bytes]:
        """ read data from socket """
        raise NotImplemented

    @abstractmethod
    def receive(self, max_len: int) -> (Optional[bytes], Optional[Address]):
        """ receive data via socket, and return it with remote address """
        raise NotImplemented


class Writer(ABC):
    """ socket writer """

    @abstractmethod
    def write(self, data: bytes) -> int:
        """ write data into socket """
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: Address) -> int:
        """ send data via socket with remote address """
        raise NotImplemented


class BaseChannel(AddressPairObject, Channel, ABC):

    def __init__(self, remote: Optional[Address], local: Optional[Address]):
        super().__init__(remote=remote, local=local)
        self.__reader = self._create_reader()
        self.__writer = self._create_writer()
        # flags
        self.__blocking = False
        self.__opened = False
        self.__connected = False
        self.__bound = False

    def __del__(self):
        # make sure the relative socket is removed
        self._set_socket(sock=None)
        self.__reader = None
        self.__writer = None

    @property  # protected
    def reader(self) -> Reader:
        return self.__reader

    @property  # protected
    def writer(self) -> Writer:
        return self.__writer

    @abstractmethod
    def _create_reader(self) -> Reader:
        """ create socket reader """
        raise NotImplemented

    @abstractmethod
    def _create_writer(self) -> Writer:
        """ create socket writer """
        raise NotImplemented

    def _refresh_flags(self, sock: Optional[socket.socket]):
        if sock is None:
            self.__blocking = False
            self.__opened = False
            self.__connected = False
            self.__bound = False
        else:
            self.__blocking = is_blocking(sock=sock)
            self.__opened = is_opened(sock=sock)
            self.__connected = is_connected(sock=sock)
            self.__bound = is_bound(sock=sock)

    @property
    def sock(self) -> Optional[socket.socket]:
        return self._get_socket()

    @abstractmethod
    def _get_socket(self) -> Optional[socket.socket]:
        """ get inner socket """
        raise NotImplemented

    @abstractmethod
    def _set_socket(self, sock: Optional[socket.socket]):
        """ change inner socket """
        # 1. check old socket
        # 2. set new socket
        # 3. refresh flags
        raise NotImplemented

    @abstractmethod
    def _close_socket(self, sock: socket.socket):
        """ close inner socket """
        raise NotImplemented

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
    def bind(self, address: Optional[Address] = None, host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
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
    def connect(self, address: Optional[Address] = None,
                host: Optional[str] = '127.0.0.1', port: Optional[int] = 0) -> socket.socket:
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
        sock = self._get_socket()
        self._set_socket(sock=None)
        return sock

    # Override
    def close(self):
        # set socket to None will refresh flags
        self._set_socket(sock=None)

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        return self.reader.read(max_len=max_len)

    # Override
    def write(self, data: bytes) -> int:
        return self.writer.write(data=data)

    # Override
    def receive(self, max_len: int) -> (Optional[bytes], Optional[Address]):
        return self.reader.receive(max_len=max_len)

    # Override
    def send(self, data: bytes, target: Address) -> int:
        return self.writer.send(data=data, target=target)
