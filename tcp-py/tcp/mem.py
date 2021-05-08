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

    def __init__(self):
        super().__init__()
        # received packages
        self.__lock = threading.Lock()
        self.__packages: List[bytes] = []
        self.__count = 0

    @property
    def length(self) -> int:
        return self.__count

    def push(self, data: bytes):
        with self.__lock:
            self.__packages.append(data)
            self.__count += len(data)

    def pop(self, max_length: int) -> Optional[bytes]:
        with self.__lock:
            assert max_length > 0, 'max length must greater than 0'
            assert len(self.__packages) > 0, 'data empty, call "get()/length()" to check data first'
            data = self.__packages.pop(0)
            data_len = len(data)
            if data_len > max_length:
                # push the remaining data back to the queue head
                self.__packages.insert(0, data[max_length:])
                data = data[:max_length]
                self.__count -= max_length
            else:
                self.__count -= data_len
            return data

    def all(self) -> Optional[bytes]:
        with self.__lock:
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
