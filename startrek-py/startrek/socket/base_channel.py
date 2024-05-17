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
import weakref
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from ..types import SocketAddress, AddressPairObject

from ..net.socket import is_blocking, is_closed, is_connected, is_bound
from ..net.socket import is_available, is_vacant
from ..net.socket import socket_bind, socket_connect, socket_disconnect
from ..net.socket import socket_send, socket_receive
from ..net import Channel, ChannelState


class SocketReader(ABC):

    @abstractmethod
    async def read(self, max_len: int) -> Optional[bytes]:
        """ read data from socket """
        raise NotImplemented

    @abstractmethod
    async def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        """ receive data via socket, and return it with remote address """
        raise NotImplemented


class SocketWriter(ABC):

    @abstractmethod
    async def write(self, data: bytes) -> int:
        """ write data into socket """
        raise NotImplemented

    @abstractmethod
    async def send(self, data: bytes, target: SocketAddress) -> int:
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

    # noinspection PyMethodMayBeStatic
    async def _socket_receive(self, sock: socket.socket, max_len: int) -> Optional[bytes]:
        # TODO: override for async receiving
        # return sock.recv(max_len)
        return socket_receive(sock=sock, max_len=max_len)

    # noinspection PyMethodMayBeStatic
    async def _socket_send(self, sock: socket.socket, data: bytes) -> int:
        # TODO: override for async sending
        # return sock.send(data)
        # return sock.sendall(data)
        return socket_send(sock=sock, data=data)


# noinspection PyAbstractClass
class ChannelReader(Controller, SocketReader, ABC):

    # Override
    async def read(self, max_len: int) -> Optional[bytes]:
        sock = self.sock
        if sock is None or is_closed(sock=sock):
            raise ConnectionError('socket closed')
        else:
            return await self._socket_receive(sock=sock, max_len=max_len)

    # @abstractmethod  # Override
    # async def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
    #     """ receive data via socket, and return it with remote address """
    #     raise NotImplemented


# noinspection PyAbstractClass
class ChannelWriter(Controller, SocketWriter, ABC):

    # Override
    async def write(self, data: bytes) -> int:
        """ Return the number of bytes sent;
            this may be less than len(data) if the network is busy. """
        sock = self.sock
        if sock is None or is_closed(sock=sock):
            raise ConnectionError('socket closed')
        else:
            return await self._socket_send(sock=sock, data=data)

    # @abstractmethod  # Override
    # async def send(self, data: bytes, target: SocketAddress) -> int:
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

    async def set_socket(self, sock: Optional[socket.socket]):
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
            await self._socket_disconnect(sock=old)

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
        sock = self.sock
        if sock is None or is_closed(sock=sock):
            return False
        elif is_bound(sock=sock) or is_connected(sock=sock):
            # alive, check reading buffer
            return self._socket_available(sock=sock)

    # noinspection PyMethodMayBeStatic
    def _socket_available(self, sock: socket.socket) -> bool:
        return is_available(sock=sock)

    @property
    def vacant(self) -> bool:
        sock = self.sock
        if sock is None or is_closed(sock=sock):
            return False
        elif is_bound(sock=sock) or is_connected(sock=sock):
            # alive, check writing buffer
            return self._socket_vacant(sock=sock)

    # noinspection PyMethodMayBeStatic
    def _socket_vacant(self, sock: socket.socket) -> bool:
        return is_vacant(sock=sock)

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

    # noinspection PyMethodMayBeStatic
    async def _socket_bind(self, sock: socket.socket, local: SocketAddress) -> bool:
        # TODO: override for async binding
        return socket_bind(sock=sock, local=local)

    # noinspection PyMethodMayBeStatic
    async def _socket_connect(self, sock: socket.socket, remote: SocketAddress) -> bool:
        # TODO: override for async connecting
        return socket_connect(sock=sock, remote=remote)

    # noinspection PyMethodMayBeStatic
    async def _socket_disconnect(self, sock: socket.socket) -> bool:
        # TODO: override for async disconnecting
        return socket_disconnect(sock=sock)

    # Override
    async def bind(self, address: Optional[SocketAddress] = None,
                   host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        if address is None:
            if port > 0:
                assert host is not None, 'host should not be empty'
                address = (host, port)
            else:
                address = self._local
                assert address is not None, 'local address not set'
        sock = self.sock
        ok = await self._socket_bind(sock=sock, local=address)
        assert ok, 'failed to bind socket: %s' % str(address)
        self._local = address
        return sock

    # Override
    async def connect(self, address: Optional[SocketAddress] = None,
                      host: Optional[str] = '127.0.0.1', port: Optional[int] = 0) -> socket.socket:
        if address is None:
            if port > 0:
                assert host is not None, 'host should not be empty'
                address = (host, port)
            else:
                address = self._remote
                assert address is not None, 'remote address not set'
        sock = self.sock
        ok = await self._socket_connect(sock=sock, remote=address)
        assert ok, 'failed to connect socket: %s' % str(address)
        self._remote = address
        return sock

    # Override
    async def disconnect(self) -> Optional[socket.socket]:
        sock = self.__sock
        if sock is not None:
            ok = await self._socket_disconnect(sock=sock)
            assert ok, 'failed to disconnect socket: %s' % sock
        return sock

    # Override
    async def close(self):
        await self.set_socket(sock=None)

    # Override
    async def read(self, max_len: int) -> Optional[bytes]:
        try:
            return await self.reader.read(max_len=max_len)
        except socket.error as error:
            await self.close()
            raise error

    # Override
    async def write(self, data: bytes) -> int:
        try:
            return await self.writer.write(data=data)
        except socket.error as error:
            await self.close()
            raise error

    # Override
    async def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        try:
            return await self.reader.receive(max_len=max_len)
        except socket.error as error:
            await self.close()
            raise error

    # Override
    async def send(self, data: bytes, target: SocketAddress) -> int:
        try:
            return await self.writer.send(data=data, target=target)
        except socket.error as error:
            await self.close()
            raise error
