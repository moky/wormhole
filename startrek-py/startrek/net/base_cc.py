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

from .channel import is_blocking
from .channel import sendall
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
    def sock(self) -> Optional[socket.socket]:
        channel = self.channel
        s = channel.sock
        assert s is not None, 'socket lost: %s' % channel
        return s

    def _check_sending_error(self, error: socket.error) -> Optional[socket.error]:
        return check_socket_error(sock=self.sock, error=error)

    def _check_receiving_error(self, error: socket.error) -> Optional[socket.error]:
        return check_socket_error(sock=self.sock, error=error)

    def _check_received_data(self, data: Optional[bytes]) -> Optional[socket.error]:
        return check_received_data(sock=self.sock, data=data)


class ChannelReader(Controller, Reader, ABC):

    # Override
    def read(self, max_len: int) -> Optional[bytes]:
        try:
            data = self.sock.recv(max_len)
        except socket.error as error:
            error = self._check_receiving_error(error=error)
            if error is not None:
                # connection lost?
                raise error
            # received nothing
            return None
        # check data
        error = self._check_received_data(data=data)
        if error is not None:
            # connection lost!
            raise error
        # OK
        return data


class ChannelWriter(Controller, Writer, ABC):

    # Override
    def write(self, data: bytes) -> int:
        try:
            # sent = sock.sendall(data)
            return sendall(data=data, sock=self.sock)
        except socket.error as error:
            error = self._check_sending_error(error=error)
            if error is not None:
                # connection lost?
                raise error
            # buffer overflow!
            return -1


#
#   Check for socket errors
#


def check_socket_error(sock: socket.socket, error: socket.error) -> Optional[socket.error]:
    # the socket will raise 'Resource temporarily unavailable'
    # when received nothing in non-blocking mode,
    # or buffer overflow while sending too many bytes,
    # here we should ignore this exception.
    if not is_blocking(sock=sock):
        # if error.errno == socket.EAGAIN:
        if error.strerror == 'Resource temporarily unavailable':
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


def check_received_data(sock: socket.socket, data: Optional[bytes]) -> Optional[socket.error]:
    # in blocking mode, the socket will wait until received something,
    # but if timeout was set, it will return None too, it's normal;
    # otherwise, we know the connection was lost.
    if data is None or len(data) == 0:
        if sock.gettimeout() is None:  # and self.blocking:
            # print('[NET] socket error: remote peer reset socket')
            return socket.error('remote peer reset socket')
