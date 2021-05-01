# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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

from abc import abstractmethod
from typing import Optional

from .status import ConnectionStatus


class Connection:

    EXPIRES = 16  # seconds

    @abstractmethod
    def send(self, data: bytes) -> int:
        """
        Send data package

        :param data: package
        :return: -1 on error
        """
        raise NotImplemented

    @abstractmethod
    def received(self) -> Optional[bytes]:
        """
        Get received data from cache, but not remove

        :return: received data
        """
        raise NotImplemented

    @abstractmethod
    def receive(self, length: int) -> Optional[bytes]:
        """
        Get received data from cache, and remove it
        (call 'received()' to check data first)

        :param length: how many bytes to receive
        :return: received data
        """
        raise NotImplemented

    @property
    def status(self) -> ConnectionStatus:
        """ Get status """
        raise NotImplemented
