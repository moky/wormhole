# -*- coding: utf-8 -*-
#
#   SHM: Shared Memory
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

import json
from multiprocessing import shared_memory
from typing import Optional, Any

from .shared import SharedMemory


class SharedMemoryCache(SharedMemory):

    def __init__(self, size: int, name: str = None, create: bool = True):
        shm = shared_memory.SharedMemory(name=name, create=create, size=size)
        super().__init__(buffer=shm.buf)
        self.__shm = shm

    @property
    def shm(self) -> shared_memory.SharedMemory:
        return self.__shm

    @property  # Override
    def buffer(self) -> bytes:
        return self.__shm.buf.tobytes()

    # Override
    def detach(self):
        self.__shm.close()

    # Override
    def remove(self):
        self.__shm.unlink()

    # Override
    def shift(self) -> Optional[Any]:
        data = self._cache.shift()
        if data is None:
            return None
        elif isinstance(data, memoryview):
            data = data.tobytes()
            return json.loads(data)
        else:
            data = data.decode('utf-8')
            return json.loads(data)
