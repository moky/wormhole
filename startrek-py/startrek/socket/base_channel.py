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

from ..net import Channel, ChannelStatus

from .helpers import SocketReader, SocketWriter
from .helpers import SocketHelper


class BaseChannel(AddressPairObject, Channel, ABC):

    def __init__(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]):
        super().__init__(remote=remote, local=local)
        # inner socket
        self.__sock: Optional[socket.socket] = None
        self.__closed = None
        # create socket helper
        self.__helper = self._create_helper()
        # create socket reader/writer
        self.__reader = self._create_reader()
        self.__writer = self._create_writer()

    #
    #   Socket Channel Controllers
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

    @abstractmethod
    def _create_helper(self) -> SocketHelper:
        raise NotImplemented

    @property  # protected
    def socket_helper(self) -> SocketHelper:
        return self.__helper

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
            helper = self.socket_helper
            await helper.disconnect(sock=old)

    #
    #   States
    #

    @property  # Override
    def status(self) -> ChannelStatus:
        if self.__closed is None:
            # initializing
            return ChannelStatus.INIT
        sock = self.sock
        helper = self.socket_helper
        if sock is None or helper.is_closed(sock=sock):
            # closed
            return ChannelStatus.CLOSED
        elif helper.is_connected(sock=sock) or helper.is_bound(sock=sock):
            # normal
            return ChannelStatus.ALIVE
        else:
            # opened
            return ChannelStatus.OPEN

    @property  # Override
    def closed(self) -> bool:
        if self.__closed is None:
            # initializing
            return False
        sock = self.sock
        helper = self.socket_helper
        return sock is None or helper.is_closed(sock=sock)

    @property  # Override
    def bound(self) -> bool:
        sock = self.sock
        helper = self.socket_helper
        return sock is not None and helper.is_bound(sock=sock)

    @property  # Override
    def connected(self) -> bool:
        sock = self.sock
        helper = self.socket_helper
        return sock is not None and helper.is_connected(sock=sock)

    @property  # Override
    def alive(self) -> bool:
        return (not self.closed) and (self.connected or self.bound)

    @property
    def available(self) -> bool:
        sock = self.sock
        helper = self.socket_helper
        if sock is None or helper.is_closed(sock=sock):
            return False
        elif helper.is_bound(sock=sock) or helper.is_connected(sock=sock):
            # alive, check reading buffer
            return helper.is_available(sock=sock)

    @property
    def vacant(self) -> bool:
        sock = self.sock
        helper = self.socket_helper
        if sock is None or helper.is_closed(sock=sock):
            return False
        elif helper.is_bound(sock=sock) or helper.is_connected(sock=sock):
            # alive, check writing buffer
            return helper.is_vacant(sock=sock)

    @property  # Override
    def blocking(self) -> bool:
        sock = self.sock
        if sock is None:
            return False
        helper = self.socket_helper
        return helper.is_blocking(sock=sock)

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
        helper = self.socket_helper
        helper.set_blocking(sock=sock, blocking=blocking)
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
        helper = self.socket_helper
        ok = helper.bind(sock=sock, local=address)
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
        helper = self.socket_helper
        ok = await helper.connect(sock=sock, remote=address)
        assert ok, 'failed to connect socket: %s' % str(address)
        self._remote = address
        return sock

    # Override
    async def disconnect(self) -> Optional[socket.socket]:
        sock = self.__sock
        if sock is not None:
            helper = self.socket_helper
            ok = await helper.disconnect(sock=sock)
            assert ok, 'failed to disconnect socket: %s' % sock
            self.__sock = None
        return sock

    # Override
    async def close(self):
        await self.set_socket(sock=None)

    # Override
    async def read(self, max_len: int) -> Optional[bytes]:
        try:
            return await self.reader.read(max_len=max_len)
        except OSError as error:
            await self.close()
            raise error

    # Override
    async def write(self, data: bytes) -> int:
        try:
            return await self.writer.write(data=data)
        except OSError as error:
            await self.close()
            raise error

    # Override
    async def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        try:
            return await self.reader.receive(max_len=max_len)
        except OSError as error:
            await self.close()
            raise error

    # Override
    async def send(self, data: bytes, target: SocketAddress) -> int:
        try:
            return await self.writer.send(data=data, target=target)
        except OSError as error:
            await self.close()
            raise error
