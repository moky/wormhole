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

import select
import socket
import weakref
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from ..types import SocketAddress, AddressPairObject

from ..net.channel import is_blocking, is_closed, is_connected, is_bound
from ..net.channel import bind_socket, connect_socket, disconnect_socket
from ..net.channel import ChannelState
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


class Controller:
    """ Socket Channel Controller """

    def __init__(self, channel):
        super().__init__()
        self.__channel = weakref.ref(channel)

    @property
    def channel(self):  # -> Optional[BaseChannel]:
        return self.__channel()

    @property
    def remote_address(self) -> Optional[SocketAddress]:
        channel = self.channel
        if isinstance(channel, BaseChannel):
            return channel.remote_address

    @property
    def local_address(self) -> Optional[SocketAddress]:
        channel = self.channel
        if isinstance(channel, BaseChannel):
            return channel.local_address

    @property
    def sock(self) -> Optional[socket.socket]:
        channel = self.channel
        if isinstance(channel, BaseChannel):
            return channel.sock


# noinspection PyAbstractClass
class ChannelReader(Controller, SocketReader, ABC):

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        sock = self.sock
        if sock is None or is_closed(sock=sock):
            raise ConnectionError('socket closed')
        else:
            return sock.recv(max_len)

    # @abstractmethod  # Override
    # def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
    #     """ receive data via socket, and return it with remote address """
    #     raise NotImplemented


# noinspection PyAbstractClass
class ChannelWriter(Controller, SocketWriter, ABC):

    # Override
    def write(self, data: bytes) -> int:
        """ Return the number of bytes sent;
            this may be less than len(data) if the network is busy. """
        # sent = sock.sendall(data)
        sock = self.sock
        if sock is None or is_closed(sock=sock):
            raise ConnectionError('socket closed')
        else:
            return sock.send(data)

    # @abstractmethod  # Override
    # def send(self, data: bytes, target: SocketAddress) -> int:
    #     """ send data via socket with remote address """
    #     raise NotImplemented


class BaseChannel(AddressPairObject, Channel, ABC):

    def __init__(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]):
        super().__init__(remote=remote, local=local)
        # inner socket
        self.__sock: Optional[socket.socket] = None
        self.__closed = None
        # create socket reader/writer
        self.__reader = self._create_reader()
        self.__writer = self._create_writer()

    #
    #   Channel Controller
    #

    @abstractmethod
    def _create_reader(self) -> SocketReader:
        """ create socket reader """
        raise NotImplemented

    @abstractmethod
    def _create_writer(self) -> SocketWriter:
        """ create socket writer """
        raise NotImplemented

    @property  # protected
    def reader(self) -> SocketReader:
        return self.__reader

    @property  # protected
    def writer(self) -> SocketWriter:
        return self.__writer

    #
    #   socket
    #

    @property
    def sock(self) -> Optional[socket.socket]:
        """ inner socket """
        return self.__sock

    def set_socket(self, sock: Optional[socket.socket]):
        """ set inner socket for this channel """
        # 1. replace with new socket
        old = self.__sock
        if sock is not None:
            self.__sock = sock
            self.__closed = False
        else:
            self.__sock = None
            self.__closed = True
        # 2. close old socket
        if old is not None and old is not sock:
            disconnect_socket(sock=old)

    #
    #   States
    #

    @property
    def state(self) -> ChannelState:
        if self.__closed is None:
            # initializing
            return ChannelState.INIT
        sock = self.sock
        if sock is None or is_closed(sock=sock):
            # closed
            return ChannelState.CLOSED
        elif is_connected(sock=sock) or is_bound(sock=sock):
            # normal
            return ChannelState.ALIVE
        else:
            # opened
            return ChannelState.OPEN

    @property  # Override
    def closed(self) -> bool:
        if self.__closed is None:
            # initializing
            return False
        sock = self.sock
        return sock is None or is_closed(sock=sock)

    @property  # Override
    def bound(self) -> bool:
        sock = self.sock
        return sock is not None and is_bound(sock=sock)

    @property  # Override
    def connected(self) -> bool:
        sock = self.sock
        return sock is not None and is_connected(sock=sock)

    @property  # Override
    def alive(self) -> bool:
        return (not self.closed) and (self.connected or self.bound)

    @property
    def available(self) -> bool:
        if not self.alive:
            return False
        sock = self.sock
        if sock is None:
            return False
        ready, _, _ = select.select([sock], [], [], 0)
        return sock in ready

    @property
    def vacant(self) -> bool:
        if not self.alive:
            return False
        sock = self.sock
        if sock is None:
            return False
        _, ready, _ = select.select([], [sock], [], 0)
        return sock in ready

    @property  # Override
    def blocking(self) -> bool:
        sock = self.sock
        return sock is not None and is_blocking(sock=sock)

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s" closed=%d bound=%d connected=%d >\n\t%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.closed, self.bound, self.connected, self.sock, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s" closed=%d bound=%d connected=%d >\n\t%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.closed, self.bound, self.connected, self.sock, cname, mod)

    # Override
    def configure_blocking(self, blocking: bool):
        sock = self.sock
        sock.setblocking(blocking)
        return sock

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
        ok = bind_socket(sock=sock, local=address)
        assert ok, 'failed to bind socket: %s' % str(address)
        self._local = address
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
        ok = connect_socket(sock=sock, remote=address)
        assert ok, 'failed to connect socket: %s' % str(address)
        self._remote = address
        return sock

    # Override
    def disconnect(self) -> Optional[socket.socket]:
        sock = self.__sock
        if sock is not None:
            ok = disconnect_socket(sock=sock)
            assert ok, 'failed to disconnect socket: %s' % sock
        return sock

    # Override
    def close(self):
        self.set_socket(sock=None)

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
