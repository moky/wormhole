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

from abc import ABC, abstractmethod
from typing import Optional


class Channel(ABC):

    @property
    def opened(self) -> bool:
        """ is_open() """
        raise NotImplemented

    @property
    def bound(self) -> bool:
        """ is_bound() """
        raise NotImplemented

    @abstractmethod
    def close(self):
        raise NotImplemented

    #
    #   Byte Channel
    #

    @abstractmethod
    def read(self, max_len: int) -> Optional[bytes]:
        """
        Reads a sequence of bytes from this channel into the given buffer.

        :param max_len: max buffer length
        :return: The number of bytes read, possibly zero,
                 or -1 if the channel has reached end-of-stream
        :raise: socket.error
        """
        raise NotImplemented

    @abstractmethod
    def write(self, data: bytes) -> int:
        """
        Writes a sequence of bytes to this channel from the given buffer.

        :param data: outgo data
        :return: The number of bytes written, possibly zero
        :raise: socket.error
        """
        raise NotImplemented

    #
    #   Selectable Channel
    #

    @abstractmethod
    def configure_blocking(self, blocking: bool):
        """
        Adjusts this channel's blocking mode.

        :param blocking: If True then this channel will be placed in blocking mode;
                         if False then it will be placed non-blocking mode
        :raise: socket.error
        """
        raise NotImplemented

    @property
    def blocking(self) -> bool:
        """ is_blocking() """
        raise NotImplemented

    #
    #   Network Channel
    #

    @abstractmethod
    def bind(self, address: Optional[tuple] = None, host: Optional[str] = '0.0.0.0', port: Optional[int] = 0):
        """
        Binds the channel's socket to a local address (host, port).

        :param address: local address
        :param host:    local host
        :param port:    local port
        :return: bound socket
        :raise: socket.error
        """
        raise NotImplemented

    @property
    def local_address(self) -> Optional[tuple]:  # (str, int)
        """
        Returns the socket address that this channel's socket is bound to.

        :return: The socket address that the socket is bound to,
                 or None if the channel's socket is not bound
        """
        raise NotImplemented

    #
    #   Socket/Datagram Channel
    #

    @property
    def connected(self) -> bool:
        """ is_connected() """
        raise NotImplemented

    @abstractmethod
    def connect(self, address: Optional[tuple] = None, host: Optional[str] = '127.0.0.1', port: Optional[int] = 0):
        """
        Connects this channel's socket.

        :param address: remote address
        :param host:    remote host
        :param port:    remote port
        :return: connected socket
        :raise: socket.error
        """
        raise NotImplemented

    @property
    def remote_address(self) -> Optional[tuple]:  # (str, int)
        """
        Returns the remote address to which this channel's socket is connected.

        :return: The remote address; None if the channel's socket is not connected
        """
        raise NotImplemented

    #
    #   Datagram Channel
    #

    @abstractmethod
    def disconnect(self):
        """
        Disconnects this channel's socket.

        :return: this socket
        :raise: socket.error
        """
        raise NotImplemented

    @abstractmethod
    def receive(self, max_len: int) -> (Optional[bytes], Optional[tuple]):
        """
        Receives a data package via this channel.

        :param max_len: max buffer length
        :return: received data and remote address
        :raise: socket.error
        """
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: tuple) -> int:
        """
        Sends a data package via this channel.

        :param data:   outgo data package
        :param target: remote address
        :return: The number of bytes sent, which will be either the number
                 of bytes that were remaining in the source buffer when this
                 method was invoked or, if this channel is non-blocking, may be
                 zero if there was insufficient room for the datagram in the
                 underlying output buffer
        :raise: socket.error
        """
        raise NotImplemented
