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
from typing import Optional, Any, Union

from .cache import CycledCache
from .shared import SharedMemory


def create_memory_cache(size: int, name: str = None):
    shm = shared_memory.SharedMemory(name=name, create=True, size=size)
    return MemoryCache(shm=shm)


class MemoryCache(CycledCache[shared_memory.SharedMemory]):

    def __init__(self, shm: shared_memory.SharedMemory):
        super().__init__(shm=shm, head_length=4)

    # Override
    def detach(self):
        self.shm.close()

    # Override
    def remove(self):
        self.shm.unlink()

    @property  # Override
    def buffer(self) -> bytes:
        return self.shm.buf.tobytes()

    @property  # Override
    def size(self) -> int:
        return self.shm.size

    # Override
    def _set(self, pos: int, value: int):
        # self.shm.buf[pos] = value
        data = bytearray(1)
        data[0] = value
        self.shm.buf[pos:(pos + 1)] = memoryview(data)

    # Override
    def _get(self, pos: int) -> int:
        return self.shm.buf[pos]

    # Override
    def _update(self, start: int, end: int, data: Union[bytes, bytearray]):
        assert start + len(data) == end, 'range error: %d + %d != %d' % (start, len(data), end)
        self.shm.buf[start:end] = data

    # Override
    def _slice(self, start: int, end: int) -> Union[bytes, bytearray]:
        return bytes(self.shm.buf[start:end])


class SharedMemoryCache(SharedMemory[shared_memory.SharedMemory]):

    def __init__(self, size: int, name: str = None):
        cache = create_memory_cache(size=size, name=name)
        super().__init__(cache=cache)

    # Override
    def shift(self) -> Optional[Any]:
        data = self.cache.shift()
        if data is None:
            return None
        elif isinstance(data, memoryview):
            data = data.tobytes()
            return json.loads(data)
        else:
            data = data.decode('utf-8')
            return json.loads(data)
