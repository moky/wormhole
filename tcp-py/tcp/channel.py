# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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
from typing import Optional, Tuple

from startrek import SocketAddress
from startrek import SocketReader, SocketWriter
from startrek import SocketHelper
from startrek import BaseChannel


class ChannelChecker:

    @classmethod
    async def check_error(cls, error: OSError, sock: socket.socket) -> Optional[OSError]:
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
            helper = SocketHelper()
            if not helper.is_blocking(sock=sock):
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
    async def check_data(cls, data: Optional[bytes], sock: socket.socket) -> Optional[OSError]:
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
                return OSError('remote peer reset socket %s' % sock)


class Controller:
    """ Socket Channel Controller """

    def __init__(self, channel):
        super().__init__()
        self.__channel = weakref.ref(channel)
        self.__helper = SocketHelper()

    @property
    def socket_helper(self) -> SocketHelper:
        return self.__helper

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


class StreamChannelReader(Controller, SocketReader):

    async def _socket_receive(self, sock: socket.socket, max_len: int) -> Optional[bytes]:
        helper = self.socket_helper
        if helper.is_closed(sock=sock):
            raise ConnectionError('socket closed')
        elif not helper.is_available(sock=sock):
            # TODO: check 'broken pipe'
            return None
        # elif helper.is_blocking(sock=sock):
        #     return sock.recv(max_len)
        else:
            return await helper.receive(sock=sock, max_len=max_len)  # raise OSError

    async def _try_read(self, max_len: int, sock: socket.socket) -> Optional[bytes]:
        try:
            # return sock.recv(max_len)
            return await self._socket_receive(sock=sock, max_len=max_len)  # raise OSError
        except OSError as error:
            error = await ChannelChecker.check_error(error=error, sock=sock)
            if error is None:
                # received nothing
                return None
            else:
                # connection lost?
                raise error
        # except Exception:
        #     return None

    # Override
    async def read(self, max_len: int) -> Optional[bytes]:
        sock = self.sock
        if sock is None:
            raise ConnectionError('channel not ready')
        # 1. try to read data
        data = await self._try_read(max_len=max_len, sock=sock)  # raise OSError
        # 2. check data
        error = await ChannelChecker.check_data(data=data, sock=sock)
        if error is not None:
            # connection lost!
            raise error
        # OK
        return data

    # Override
    async def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        data = await self.read(max_len=max_len)
        if data is None or len(data) == 0:
            return None, None
        else:
            return data, self.remote_address


class StreamChannelWriter(Controller, SocketWriter):

    async def _socket_send(self, sock: socket.socket, data: bytes) -> int:
        helper = self.socket_helper
        if helper.is_closed(sock=sock):
            raise ConnectionError('socket closed')
        # elif not helper.is_vacant(sock=sock):
        #     # TODO: check 'broken pipe'
        #     return -1
        # elif helper.is_blocking(sock=sock):
        #     return sock.send(data)
        else:
            return await helper.send(sock=sock, data=data)  # raise OSError

    async def _try_write(self, data: bytes, sock: socket.socket) -> int:
        try:
            # return sock.send(data)
            return await self._socket_send(sock=sock, data=data)  # raise OSError
        except OSError as error:
            error = await ChannelChecker.check_error(error=error, sock=sock)
            if error is not None:
                # connection lost?
                raise error
            # buffer overflow!
            return 0
        # except Exception:
        #     return -1

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
            cnt = await self._try_write(data=data, sock=sock)  # raise OSError
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

    # Override
    async def send(self, data: bytes, target: SocketAddress) -> int:
        # TCP channel will be always connected
        # so the target address must be the remote address
        remote = self.remote_address
        assert target is None or target == remote, 'target error: %s, remote=%s' % (target, remote)
        return await self.write(data=data)


class StreamChannel(BaseChannel):
    """ Stream Channel """

    # Override
    def _create_reader(self) -> SocketReader:
        return StreamChannelReader(channel=self)

    # Override
    def _create_writer(self) -> SocketWriter:
        return StreamChannelWriter(channel=self)
