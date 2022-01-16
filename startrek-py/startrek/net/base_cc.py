# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2022 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2022 Albert Moky
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
from abc import ABC
from typing import Optional

from ..types import Address

from .channel import is_blocking
from .base_channel import Reader, Writer, BaseChannel


#
#   Socket Channel Controller
#   ~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Reader, Writer, ErrorChecker
#


class Controller:

    def __init__(self, channel: BaseChannel):
        super().__init__()
        self.__channel = weakref.ref(channel)

    @property
    def channel(self) -> BaseChannel:
        return self.__channel()

    @property
    def remote_address(self) -> Optional[Address]:
        return self.channel.remote_address

    @property
    def local_address(self) -> Optional[Address]:
        return self.channel.local_address

    @property
    def sock(self) -> Optional[socket.socket]:
        s = self.channel.sock
        if s is None:
            raise socket.error('socket lost: %s' % self.channel)
        return s

    def _check_error(self, error: socket.error, sock: socket.socket = None) -> Optional[socket.error]:
        if sock is None:
            sock = self.sock
        # the socket will raise 'Resource temporarily unavailable'
        # when received nothing in non-blocking mode,
        # or buffer overflow while sending too many bytes,
        # here we should ignore this exception.
        if error.errno == socket.EAGAIN:  # error.strerror == 'Resource temporarily unavailable':
            if not is_blocking(sock=sock):
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


class ChannelReader(Controller, Reader, ABC):

    def _check_data(self, data: Optional[bytes], sock: socket.socket = None) -> Optional[socket.error]:
        # in blocking mode, the socket will wait until received something,
        # but if timeout was set, it will return None too, it's normal;
        # otherwise, we know the connection was lost.
        if data is None or len(data) == 0:
            if sock is None:
                sock = self.sock
            if sock.gettimeout() is None:  # and self.blocking:
                # print('[NET] socket error: remote peer reset socket %s' % sock)
                return socket.error('remote peer reset socket %s' % sock)

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        sock = self.sock
        try:
            data = sock.recv(max_len)
        except socket.error as error:
            error = self._check_error(error=error, sock=sock)
            if error is not None:
                # connection lost?
                raise error
            # received nothing
            data = None
        # check data
        error = self._check_data(data=data, sock=sock)
        if error is not None:
            # connection lost!
            raise error
        # OK
        return data


class ChannelWriter(Controller, Writer, ABC):

    def _try_send(self, data: bytes, sock: socket.socket) -> int:
        try:
            return sock.send(data)
        except socket.error as error:
            error = self._check_error(error=error, sock=sock)
            if error is None:
                # buffer overflow!
                return -1
            else:
                # connection lost?
                raise error

    # Override
    def write(self, data: bytes) -> int:
        """ Return the number of bytes sent;
            this may be less than len(data) if the network is busy. """
        # sent = sock.sendall(data)
        sock = self.sock
        sent = 0
        rest = len(data)
        # assert rest > 0, 'cannot send empty data'
        while True:  # is_opened(sock=sock):
            cnt = self._try_send(data=data, sock=sock)
            # check send result
            if cnt == 0:
                # buffer overflow?
                break
            elif cnt < 0:
                # buffer overflow!
                if sent == 0:
                    return -1
                break
            # something sent, check remaining data
            sent += cnt
            rest -= cnt
            if rest > 0:
                data = data[cnt:]
            else:
                break  # done!
        return sent
