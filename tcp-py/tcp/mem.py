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

import threading
from typing import Optional, List

from .pool import Pool


class MemPool(Pool):

    """
        Max length of memory cache
        ~~~~~~~~~~~~~~~~~~~~~~~~~~
    """
    MAX_CACHE_LENGTH = 1024 * 1024 * 1024  # 1GB

    def __init__(self):
        super().__init__()
        # received packages
        self.__packages: List[bytes] = []
        self.__packages_lock = threading.Lock()

    def __is_full(self) -> bool:
        length = 0
        for pack in self.__packages:
            length += len(pack)
        return length >= self.MAX_CACHE_LENGTH

    @property
    def is_full(self) -> bool:
        with self.__packages_lock:
            return self.__is_full()

    def cache(self, data: bytes) -> Optional[bytes]:
        ejected = None
        with self.__packages_lock:
            # 1. check memory cache status
            if self.__is_full():
                ejected = self.__packages.pop(0)
            # 2. append the new package to the end
            self.__packages.append(data)
        return ejected

    def received(self) -> Optional[bytes]:
        with self.__packages_lock:
            count = len(self.__packages)
            if count == 1:
                return self.__packages[0]
            elif count > 1:
                data = b''
                for pack in self.__packages:
                    data += pack
                self.__packages.clear()
                self.__packages.append(data)
                return data

    def receive(self, length: int) -> Optional[bytes]:
        with self.__packages_lock:
            if len(self.__packages) > 0:
                data = self.__packages.pop(0)
                if len(data) > length:
                    # push the remaining data back to the queue head
                    self.__packages.insert(0, data[length:])
                    data = data[:length]
                return data
