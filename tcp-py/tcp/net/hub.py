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

from abc import ABC, abstractmethod
from typing import Optional

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
    def receive(self, source: Optional[tuple], destination: Optional[tuple]) -> Optional[bytes]:
        """
        Receive data via the connection bound to source and connected to destination

        :param source:      from address (remote);
                            if it's None, receive from any connection connected to destination
        :param destination: to address (local);
                            if it's None, receive from any connection bound to source
        :return: data received
        """
        raise NotImplemented

    @abstractmethod
    def get_connection(self, remote: tuple, local: tuple) -> Optional[Connection]:
        """
        Get connection if already exists

        :param remote: remote address
        :param local:  local address
        :return: None on connection not found
        """
        raise NotImplemented

    @abstractmethod
    def connect(self, remote: tuple, local: tuple) -> Optional[Connection]:
        """
        Get/create connection

        :param remote: remote address
        :param local:  local address
        :return: None on error
        """
        raise NotImplemented

    @abstractmethod
    def disconnect(self, remote: tuple, local: tuple):
        """
        Close connection

        :param remote: remote address
        :param local:  local address
        """
        raise NotImplemented
