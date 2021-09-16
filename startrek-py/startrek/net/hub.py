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
from typing import Optional, Set

from ..fsm import Processor

from .channel import Channel
from .connection import Connection


class Hub(Processor, ABC):
    """ Connections & Channels Container """

    @abstractmethod
    def open(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Channel]:
        """
        Open a channel with direction (remote, local)

        :param remote: remote address to connected
        :param local:  local address to bound
        :return: None on socket error
        """
        raise NotImplemented

    @abstractmethod
    def close(self, channel: Channel):
        """
        Close socket channel

        :param channel: socket channel
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Optional[Connection]:
        """
        Get connection with direction (remote, local)

        :param remote: remote address
        :param local:  local address
        :return: None on channel not opened
        """
        raise NotImplemented

    @abstractmethod
    def disconnect(self, connection: Connection):
        """
        Close connection

        :param connection: closing connection
        """
        raise NotImplemented

    #
    #   Local Address
    #

    @classmethod
    def host_name(cls) -> str:
        return socket.gethostname()

    @classmethod
    def addr_info(cls):  # -> List[Tuple[Union[AddressFamily, int], Union[SocketKind, int], int, str, Tuple[Any, ...]]]
        host = socket.gethostname()
        if host is not None:
            try:
                return socket.getaddrinfo(host, None)
            except socket.error as error:
                print('[NET] failed to get address info: %s' % error)
                return []

    @classmethod
    def inet_addresses(cls) -> Set[str]:
        addresses = set()
        info = cls.addr_info()
        for item in info:
            addresses.add(item[4][0])
        return addresses

    @classmethod
    def inet_address(cls) -> Optional[str]:
        # get from addr info
        info = cls.addr_info()
        for item in info:
            ip = item[4][0]
            if ':' not in ip and '127.0.0.1' != ip:
                return ip
        # get from UDP socket
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            remote = ('8.8.8.8', 8888)
            sock.connect(remote)
            ip = sock.getsockname()[0]
        finally:
            if sock is not None:
                sock.close()
        return ip
