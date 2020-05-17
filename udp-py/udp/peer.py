# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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

"""
    Peer
    ~~~~

    Network Node
"""

from abc import ABC, abstractmethod
from typing import Union


class Delegate(ABC):

    @abstractmethod
    def send(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
        """
        Send data to destination address

        :param data:        data package to send
        :param destination: remote address
        :param source:      local address or port number
        :return: data length sent, -1 on error
        """
        raise NotImplemented

    @abstractmethod
    def received(self, data: bytes, source: tuple, destination: Union[tuple, int]):
        """
        Handle received data from source address

        :param data:        data package received
        :param source:      remote address
        :param destination: local address or port number
        """
        raise NotImplemented


class Peer:

    def __init__(self):
        super().__init__()
        self.delegate: Delegate = None
