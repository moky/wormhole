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
from abc import ABC, abstractmethod
from typing import Optional, Set

from .connection import Connection


"""
    Topology
    ~~~~~~~~

                            +---------------+
                            |      APP      |
                            +---------------+
                                |       A
                                |       |  (filter)
                                V       |
            +-----------------------------------------------+
            |                                               |
            |     +----------+     HUB     +----------+     |
            |     |  socket  |             |  socket  |     |
            +-----+----------+-------------+----------+-----+
                     |    A                   |  |  A
                     |    |   (connections)   |  |  |
                     |    |    (+channels)    |  |  |
                     |    |                   |  |  |
            ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
            ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
                     |    |                   |  |  |
                     V    |                   V  V  |
"""


class Hub(ABC):

    @abstractmethod
    def send(self, data: bytes, source: Optional[tuple], destination: tuple) -> bool:
        """
        Send data from source to destination

        :param data:        payload
        :param source:      from address (local);
                            if it's None, send via any connection connected to destination
        :param destination: to address (remote)
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def get_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Connection]:
        """
        Get connection if already exists

        :param remote: remote address
        :param local:  local address
        :return: None on connection not found
        """
        raise NotImplemented

    @abstractmethod
    def connect(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Connection]:
        """
        Get/create connection

        :param remote: remote address
        :param local:  local address
        :return: None on error
        """
        raise NotImplemented

    @abstractmethod
    def disconnect(self, remote: Optional[tuple], local: Optional[tuple]):
        """
        Close connection

        :param remote: remote address
        :param local:  local address
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
            return socket.getaddrinfo(host, None)

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
