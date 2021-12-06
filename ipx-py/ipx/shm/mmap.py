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

import mmap
import os
from typing import Union

from .cache import CycledCache
from .shared import SharedMemory


def create_memory_cache(size: int, name: str = None):
    if os.name == 'nt':
        # Windows
        access = mmap.ACCESS_DEFAULT
        shm = mmap.mmap(fileno=-1, length=size, tagname=name, access=access, offset=0)
    else:
        # Unix
        flags = mmap.MAP_SHARED
        prot = mmap.PROT_READ | mmap.PROT_WRITE
        access = mmap.ACCESS_DEFAULT
        shm = mmap.mmap(fileno=-1, length=size, flags=flags, prot=prot, access=access, offset=0)
    return MemoryCache(shm=shm)


class MemoryCache(CycledCache[mmap.mmap]):

    def __init__(self, shm: mmap.mmap):
        super().__init__(shm=shm, head_length=4)

    # Override
    def detach(self):
        self.shm.close()

    # Override
    def remove(self):
        self.shm.close()

    @property  # Override
    def buffer(self) -> bytes:
        return bytes(self.shm)

    @property  # Override
    def size(self) -> int:
        # return self.shm.size()
        return len(self.shm)

    # Override
    def _set(self, pos: int, value: int):
        self.shm[pos] = value

    # Override
    def _get(self, pos: int) -> int:
        return self.shm[pos]

    # Override
    def _update(self, start: int, end: int, data: Union[bytes, bytearray]):
        assert start + len(data) == end, 'range error: %d + %d != %d' % (start, len(data), end)
        self.shm[start:end] = data

    # Override
    def _slice(self, start: int, end: int) -> Union[bytes, bytearray]:
        return self.shm[start:end]


class SharedMemoryCache(SharedMemory[mmap.mmap]):

    def __init__(self, size: int, name: str = None):
        cache = create_memory_cache(size=size, name=name)
        super().__init__(cache=cache)
