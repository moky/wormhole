# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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
from typing import Optional, Tuple

from startrek.types import SocketAddress
from startrek import BaseChannel, ChannelReader, ChannelWriter

from .aio import is_blocking, is_closed, is_available
from .aio import socket_send, socket_receive
from .aio import socket_send_to, socket_receive_from
from .aio import socket_bind, socket_connect, socket_disconnect


class ChannelChecker:

    @classmethod
    async def check_error(cls, error: socket.error, sock: socket.socket) -> Optional[socket.error]:
        """
            Check socket error

               (1) check E_AGAIN
                   the socket will raise 'Resource temporarily unavailable'
                   when received nothing in non-blocking mode,
                   or buffer overflow while sending too many bytes,
                   here we should ignore this exception.
               (2) check timeout
                   in blocking mode, the socket will wait until send/received data,
                   but if timeout was set, it will raise 'timeout' error on timeout,
                   here we should ignore this exception
        """
        # the socket will raise 'Resource temporarily unavailable'
        # when received nothing in non-blocking mode,
        # or buffer overflow while sending too many bytes,
        # here we should ignore this exception.
        if error.errno == socket.EAGAIN:  # error.strerror == 'Resource temporarily unavailable':
            if not await is_blocking(sock=sock):
                # ignore it
                return None
        # in blocking mode, the socket wil wait until sent/received data,
        # but if timeout was set, it will raise 'timeout' error on timeout,
        # here we should ignore this exception.
        if isinstance(error, socket.timeout):
            if sock.gettimeout() is not None:  # or not self.blocking:
                # ignore it
                return None
        # print('[NET] socket error: %s' % error)
        return error

    @classmethod
    async def check_data(cls, data: Optional[bytes], sock: socket.socket) -> Optional[socket.error]:
        """
            Check data received from socket

            (1) check timeout
                in blocking mode, the socket will wait until received something,
                but if timeout was set, it will return nothing too, it's normal;
                otherwise, we know the connection was lost.
        """
        # in blocking mode, the socket will wait until received something,
        # but if timeout was set, it will return None too, it's normal;
        # otherwise, we know the connection was lost.
        if data is None or len(data) == 0:
            if sock.gettimeout() is None:  # and self.blocking:
                # print('[NET] socket error: remote peer reset socket %s' % sock)
                return socket.error('remote peer reset socket %s' % sock)


class PacketChannelReader(ChannelReader):
    """ Datagram Packet Channel Reader """

    # Override
    async def _socket_receive(self, sock: socket.socket, max_len: int) -> Optional[bytes]:
        if await is_closed(sock=sock):
            raise ConnectionError('socket closed')
        elif not await is_available(sock=sock):
            # TODO: check 'broken pipe'
            return None
        elif await is_blocking(sock=sock):
            return await super()._socket_receive(sock=sock, max_len=max_len)
        else:
            return await socket_receive(sock=sock, max_len=max_len)

    # noinspection PyMethodMayBeStatic
    async def _socket_receive_from(self, sock: socket.socket, max_len: int
                                   ) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        if await is_closed(sock=sock):
            raise ConnectionError('socket closed')
        elif not await is_available(sock=sock):
            # TODO: check 'broken pipe'
            return None, None
        else:
            # return sock.recvfrom(max_len)
            return await socket_receive_from(sock=sock, max_len=max_len)

    # noinspection PyMethodMayBeStatic
    async def _try_read(self, max_len: int, sock: socket.socket) -> Optional[bytes]:
        try:
            # return sock.recv(max_len)
            return await self._socket_receive(sock=sock, max_len=max_len)
        except socket.error as error:
            error = await ChannelChecker.check_error(error=error, sock=sock)
            if error is None:
                # received nothing
                return None
            else:
                # connection lost?
                raise error

    # Override
    async def read(self, max_len: int) -> Optional[bytes]:
        sock = self.sock
        if sock is None:
            raise ConnectionError('channel not ready')
        # 1. try to read data
        data = await self._try_read(max_len=max_len, sock=sock)
        # 2. check data
        error = await ChannelChecker.check_data(data=data, sock=sock)
        if error is not None:
            # connection lost!
            raise error
        # OK
        return data

    # noinspection PyMethodMayBeStatic
    async def _try_receive(self, max_len: int, sock: socket.socket) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        try:
            # return sock.recvfrom(max_len)
            return await self._socket_receive_from(sock=sock, max_len=max_len)
        except socket.error as error:
            error = await ChannelChecker.check_error(error=error, sock=sock)
            if error is None:
                # received nothing
                return None, None
            else:
                # connection lost?
                raise error

    async def _receive_from(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        sock = self.sock
        if sock is None:
            raise ConnectionError('channel not ready')
        data, remote = await self._try_receive(max_len=max_len, sock=sock)
        # check data
        error = await ChannelChecker.check_data(data=data, sock=sock)
        if error is None:
            # OK
            return data, remote
        else:
            # connection lost!
            raise error

    # Override
    async def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        remote = self.remote_address
        if remote is None:
            # not connect (UDP)
            return await self._receive_from(max_len=max_len)
        else:
            # connected (TCP/UDP)
            return await self.read(max_len=max_len), remote


class PacketChannelWriter(ChannelWriter):
    """ Datagram Packet Channel Writer """

    # Override
    async def _socket_send(self, sock: socket.socket, data: bytes) -> int:
        if await is_closed(sock=sock):
            raise ConnectionError('socket closed')
        # elif not await is_vacant(sock=sock):
        #     # TODO: check 'broken pipe'
        #     return -1
        elif await is_blocking(sock=sock):
            return await super()._socket_send(sock=sock, data=data)
        else:
            return await socket_send(sock=sock, data=data)

    # noinspection PyMethodMayBeStatic
    async def _socket_send_to(self, sock: socket.socket, data: bytes, target: SocketAddress) -> int:
        if await is_closed(sock=sock):
            raise ConnectionError('socket closed')
        # elif not await is_vacant(sock=sock):
        #     # TODO: check 'broken pipe'
        #     return -1
        else:
            # return sock.sendto(data, remote)
            return await socket_send_to(sock=sock, data=data, target=target)

    # noinspection PyMethodMayBeStatic
    async def _try_write(self, data: bytes, sock: socket.socket) -> int:
        try:
            # return sock.send(data)
            return await self._socket_send(sock=sock, data=data)
        except socket.error as error:
            error = await ChannelChecker.check_error(error=error, sock=sock)
            if error is not None:
                # connection lost?
                raise error
            # buffer overflow!
            return 0

    # Override
    async def write(self, data: bytes) -> int:
        """ Return the number of bytes sent;
            this may be less than len(data) if the network is busy. """
        sock = self.sock
        if sock is None:
            raise ConnectionError('channel not ready')
        # sent = sock.sendall(data)
        sent = 0
        rest = len(data)
        # assert rest > 0, 'cannot send empty data'
        while True:  # while is_opened(sock=sock):
            cnt = await self._try_write(data=data, sock=sock)
            # check send result
            if cnt <= 0:
                # buffer overflow?
                break
            # something sent, check remaining data
            sent += cnt
            rest -= cnt
            if rest <= 0:
                # done!
                break
            else:
                # remove sent part
                data = data[cnt:]
        # OK
        if sent > 0:
            return sent
        elif cnt < 0:
            assert cnt == -1, 'sent error: %d' % cnt
            return -1
        else:
            return 0

    # noinspection PyMethodMayBeStatic
    async def _try_send(self, data: bytes, target: SocketAddress, sock: socket.socket) -> int:
        try:
            # return sock.sendto(data, target)
            return await self._socket_send_to(sock=sock, data=data, target=target)
        except socket.error as error:
            error = await ChannelChecker.check_error(error=error, sock=sock)
            if error is None:
                # buffer overflow!
                return -1
            else:
                # connection lost?
                raise error

    # Override
    async def send(self, data: bytes, target: SocketAddress) -> int:
        remote = self.remote_address
        if remote is None:
            # not connect (UDP)
            assert target is not None, 'target missed for unbound channel'
            return await self._try_send(data=data, target=target, sock=self.sock)
        else:
            # connected (TCP/UDP)
            remote = self.remote_address
            assert target is None or target == remote, 'target error: %s, remote=%s' % (target, remote)
            # return sock.send(data)
            return await self._try_write(data=data, sock=self.sock)


class PacketChannel(BaseChannel):
    """ Datagram Packet Channel """

    # Override
    def _create_reader(self):
        return PacketChannelReader(channel=self)

    # Override
    def _create_writer(self):
        return PacketChannelWriter(channel=self)

    # Override
    async def _socket_bind(self, sock: socket.socket, local: SocketAddress) -> bool:
        return await socket_bind(sock=sock, local=local)

    # Override
    async def _socket_connect(self, sock: socket.socket, remote: SocketAddress) -> bool:
        return await socket_connect(sock=sock, remote=remote)

    # Override
    async def _socket_disconnect(self, sock: socket.socket) -> bool:
        return await socket_disconnect(sock=sock)
