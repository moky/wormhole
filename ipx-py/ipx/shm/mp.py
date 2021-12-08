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

from multiprocessing import shared_memory
from typing import Optional, Any, Union

from ..mem import GiantQueue
from .shared import SharedMemory
from .shared import SharedMemoryController


def create_shared_memory(size: int, name: str = None):
    return shared_memory.SharedMemory(name=name, create=True, size=size)


class MPSharedMemory(SharedMemory):

    def __init__(self, size: int, name: str = None):
        super().__init__()
        self.__shm = create_shared_memory(size=size, name=name)

    @property
    def shm(self) -> shared_memory.SharedMemory:
        return self.__shm

    @property  # Override
    def buffer(self) -> bytes:
        return self.shm.buf.tobytes()

    @property  # Override
    def size(self) -> int:
        return self.shm.size

    # Override
    def detach(self):
        self.shm.close()

    # Override
    def destroy(self):
        self.shm.unlink()

    # Override
    def get_byte(self, index: int) -> int:
        return self.shm.buf[index]

    # Override
    def get_bytes(self, start: int = 0, end: int = None) -> Optional[bytes]:
        if end is None:
            end = self.size
        if 0 <= start < end <= self.size:
            return bytes(self.shm.buf[start:end])

    # Override
    def set_byte(self, index: int, value: int):
        # self.shm.buf[pos] = value
        data = bytearray(1)
        data[0] = value
        self.shm.buf[index:(index + 1)] = memoryview(data)

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
            self.shm.buf[start:end] = source


class MpSharedMemoryController(SharedMemoryController):

    # Override
    def shift(self) -> Optional[Any]:
        data = self.queue.shift()
        if isinstance(data, memoryview):
            data = data.tobytes()
        if data is not None:
            return self._decode(data=data)

    @classmethod
    def new(cls, size: int, name: str = None):
        shm = MPSharedMemory(size=size, name=name)
        queue = GiantQueue(memory=shm)
        return cls(queue=queue)
