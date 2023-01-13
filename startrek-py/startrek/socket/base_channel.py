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
from typing import Optional, Tuple

from ..types import Address, AddressPairObject

from ..net.channel import is_blocking, is_opened, is_connected, is_bound
from ..net import Channel


class SocketReader(ABC):

    @abstractmethod
    def read(self, max_len: int) -> Optional[bytes]:
        """ read data from socket """
        raise NotImplemented

    @abstractmethod
    def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[Address]]:
        """ receive data via socket, and return it with remote address """
        raise NotImplemented


class SocketWriter(ABC):

    @abstractmethod
    def write(self, data: bytes) -> int:
        """ write data into socket """
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: Address) -> int:
        """ send data via socket with remote address """
        raise NotImplemented


class BaseChannel(AddressPairObject, Channel, ABC):

    def __init__(self, remote: Optional[Address], local: Optional[Address], sock: socket.socket):
        super().__init__(remote=remote, local=local)
        # flags
        self.__blocking = False
        self.__opened = False
        self.__connected = False
        self.__bound = False
        self.__sock = sock
        self._refresh_flags()
        # socket reader/writer
        self.__reader = self._create_reader()
        self.__writer = self._create_writer()

    def __del__(self):
        # make sure the relative socket is removed
        self.__remove_socket()
        self.__reader = None
        self.__writer = None

    @property  # protected
    def reader(self) -> SocketReader:
        return self.__reader

    @property  # protected
    def writer(self) -> SocketWriter:
        return self.__writer

    @abstractmethod
    def _create_reader(self) -> SocketReader:
        """ create socket reader """
        raise NotImplemented

    @abstractmethod
    def _create_writer(self) -> SocketWriter:
        """ create socket writer """
        raise NotImplemented

    @property
    def sock(self) -> Optional[socket.socket]:
        return self.__sock

    def __remove_socket(self):
        # 1. clear inner socket
        sock: socket.socket = self.__sock
        self.__sock = None
        # 2. refresh flags
        self._refresh_flags()
        # 3. close old socket
        if sock is not None and is_opened(sock=sock):
            sock.close()

    def _refresh_flags(self):
        """ refresh flags with inner socket """
        sock = self.__sock
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
    def closed(self) -> bool:
        return not self.__opened

    @property  # Override
    def connected(self) -> bool:
        return self.__connected

    @property  # Override
    def bound(self) -> bool:
        return self.__bound

    @property  # Override
    def alive(self) -> bool:
        return (not self.closed) and (self.connected or self.bound)

    @property  # Override
    def remote_address(self) -> Address:  # (str, int)
        return self._remote

    @property  # Override
    def local_address(self) -> Optional[Address]:  # (str, int)
        return self._local

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s">\n\t%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.__sock, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s">\n\t%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.__sock, cname, mod)

    # Override
    def bind(self, address: Optional[Address] = None,
             host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        if address is None:
            if port > 0:
                address = (host, port)
            else:
                address = self._local
                assert address is not None, 'local address not set'
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
            if port > 0:
                address = (host, port)
            else:
                address = self._remote
                assert address is not None, 'remote address not set'
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
        if sock is not None and is_connected(sock=sock):
            try:
                sock.close()
                self.__sock = None
            finally:
                self._refresh_flags()
        return sock

    # Override
    def close(self):
        # set socket to None and refresh flags
        self.__remove_socket()

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        try:
            return self.reader.read(max_len=max_len)
        except socket.error as error:
            self.close()
            raise error

    # Override
    def write(self, data: bytes) -> int:
        try:
            return self.writer.write(data=data)
        except socket.error as error:
            self.close()
            raise error

    # Override
    def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[Address]]:
        try:
            return self.reader.receive(max_len=max_len)
        except socket.error as error:
            self.close()
            raise error

    # Override
    def send(self, data: bytes, target: Address) -> int:
        try:
            return self.writer.send(data=data, target=target)
        except socket.error as error:
            self.close()
            raise error
