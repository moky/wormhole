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

from ..types import SocketAddress, AddressPairObject

from ..net.channel import is_blocking, is_closed, is_connected, is_bound
# from ..net.channel import get_remote_address, get_local_address
from ..net.channel import close_socket
from ..net import Channel


class SocketReader(ABC):

    @abstractmethod
    def read(self, max_len: int) -> Optional[bytes]:
        """ read data from socket """
        raise NotImplemented

    @abstractmethod
    def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        """ receive data via socket, and return it with remote address """
        raise NotImplemented


class SocketWriter(ABC):

    @abstractmethod
    def write(self, data: bytes) -> int:
        """ write data into socket """
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: SocketAddress) -> int:
        """ send data via socket with remote address """
        raise NotImplemented


class BaseChannel(AddressPairObject, Channel, ABC):

    def __init__(self, remote: Optional[SocketAddress], local: Optional[SocketAddress], sock: socket.socket):
        super().__init__(remote=remote, local=local)
        # flags
        self.__blocking = False
        # self.__closed = False
        self.__connected = False
        self.__bound = False
        self.__sock = sock
        self._refresh_flags()
        # socket reader/writer
        self.__reader = self._create_reader()
        self.__writer = self._create_writer()

    def __del__(self):
        # make sure the relative socket is removed
        self._set_socket(sock=None)
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
        return self._get_socket()

    def _get_socket(self) -> Optional[socket.socket]:
        return self.__sock

    def _set_socket(self, sock: Optional[socket.socket]):
        # 1. replace with new socket
        old = self.__sock
        self.__sock = sock
        # 2. refresh flags
        self._refresh_flags()
        # 3. close old socket
        if not (old is None or old is sock):
            close_socket(sock=old)

    def _refresh_flags(self):
        """ refresh flags with inner socket """
        sock = self._get_socket()
        if sock is None:
            self.__blocking = False
            # self.__closed = False
            self.__connected = False
            self.__bound = False
        else:
            self.__blocking = is_blocking(sock=sock)
            # self.__closed = is_closed(sock=sock)
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
        # return self.__closed
        sock = self._get_socket()
        return sock is None or is_closed(sock=sock)

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
    def remote_address(self) -> SocketAddress:  # (str, int)
        address = self._remote
        # if address is None:
        #     sock = self._get_socket()
        #     if sock is not None:
        #         address = get_remote_address(sock=sock)
        return address

    @property  # Override
    def local_address(self) -> Optional[SocketAddress]:  # (str, int)
        address = self._local
        # if address is None:
        #     sock = self._get_socket()
        #     if sock is not None:
        #         address = get_local_address(sock=sock)
        return address

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s">\n\t%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self._get_socket(), cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s">\n\t%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self._get_socket(), cname, mod)

    # Override
    def bind(self, address: Optional[SocketAddress] = None,
             host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        if address is None:
            if port > 0:
                assert host is not None, 'host should not be empty'
                address = (host, port)
            else:
                address = self._local
                assert address is not None, 'local address not set'
        sock = self.sock
        if sock is None:
            raise socket.error('cannot bind socket: local=(%s:%d)' % address)
        # self.__closed = False
        self.__blocking = is_blocking(sock=sock)
        sock.bind(address)
        self._local = address
        self.__bound = True
        return sock

    # Override
    def connect(self, address: Optional[SocketAddress] = None,
                host: Optional[str] = '127.0.0.1', port: Optional[int] = 0) -> socket.socket:
        if address is None:
            if port > 0:
                assert host is not None, 'host should not be empty'
                address = (host, port)
            else:
                address = self._remote
                assert address is not None, 'remote address not set'
        sock = self.sock
        if sock is None:
            raise socket.error('cannot connect socket: remote=(%s:%d)' % address)
        # self.__closed = False
        self.__blocking = is_blocking(sock=sock)
        sock.connect(address)
        self._remote = address
        self.__connected = True
        return sock

    # Override
    def disconnect(self) -> Optional[socket.socket]:
        # 1. clear inner socket
        sock = self.__sock
        self.__sock = None
        # 2. refresh flags
        self._refresh_flags()
        # 3. close connected socket
        if sock is not None and is_connected(sock=sock):
            close_socket(sock=sock)
        return sock

    # Override
    def close(self):
        # set socket to None and refresh flags
        self._set_socket(sock=None)

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
    def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        try:
            return self.reader.receive(max_len=max_len)
        except socket.error as error:
            self.close()
            raise error

    # Override
    def send(self, data: bytes, target: SocketAddress) -> int:
        try:
            return self.writer.send(data=data, target=target)
        except socket.error as error:
            self.close()
            raise error
