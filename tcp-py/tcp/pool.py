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

from abc import ABC, abstractmethod
from typing import Optional


class Pool(ABC):

    """
        Memory cache for received data
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    @abstractmethod
    def push(self, data: bytes):
        """
        Add received data to cache

        :param data: received data
        """
        raise NotImplemented

    @abstractmethod
    def pop(self, max_length: int) -> Optional[bytes]:
        """
        Get received data from pool with max length (remove)
        (must call 'get()/length()' to check data length first)

        :param max_length: max data length to remove
        :return: remove data from the pool and return it
        """
        raise NotImplemented

    @abstractmethod
    def all(self) -> Optional[bytes]:
        """
        Get all received  data (not remove)

        :return: received data, None on cache pool empty
        """
        raise NotImplemented

    @property
    def length(self) -> int:
        """ Get length of cached bytes """
        raise NotImplemented
