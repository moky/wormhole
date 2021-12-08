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
from typing import Union, Optional

from ..mem import GiantQueue
from .shared import SharedMemory
from .shared import SharedMemoryController


def create_shared_memory(size: int, name: str = None) -> mmap.mmap:
    if os.name == 'nt':
        # Windows
        access = mmap.ACCESS_DEFAULT
        return mmap.mmap(fileno=-1, length=size, tagname=name, access=access, offset=0)
    else:
        # Unix
        flags = mmap.MAP_SHARED
        prot = mmap.PROT_READ | mmap.PROT_WRITE
        access = mmap.ACCESS_DEFAULT
        return mmap.mmap(fileno=-1, length=size, flags=flags, prot=prot, access=access, offset=0)


class MmapSharedMemory(SharedMemory):

    def __init__(self, size: int, name: str = None):
        super().__init__()
        self.__shm = create_shared_memory(size=size, name=name)

    @property
    def shm(self) -> mmap.mmap:
        return self.__shm

    @property  # Override
    def buffer(self) -> bytes:
        return bytes(self.shm)

    @property  # Override
    def size(self) -> int:
        return len(self.shm)

    # Override
    def detach(self):
        self.shm.close()

    # Override
    def destroy(self):
        self.shm.close()

    # Override
    def get_byte(self, index: int) -> int:
        return self.shm[index]

    # Override
    def get_bytes(self, start: int = 0, end: int = None) -> Optional[bytes]:
        if end is None:
            end = self.size
        if 0 <= start < end <= self.size:
            return self.shm[start:end]

    # Override
    def set_byte(self, index: int, value: int):
        self.shm[index] = value

    # Override
    def update(self, index: int, source: Union[bytes, bytearray], start: int = 0, end: int = None):
        src_len = len(source)
        if end is None:
            end = src_len
        if start < end:
            if 0 < start or end < src_len:
                source = source[start:end]
            start += index
            end += index
            self.shm[start:end] = source


class MmapSharedMemoryController(SharedMemoryController):

    @classmethod
    def new(cls, size: int, name: str = None):
        shm = MmapSharedMemory(size=size, name=name)
        queue = GiantQueue(memory=shm)
        return cls(queue=queue)
