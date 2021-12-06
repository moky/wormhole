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

from typing import Union

import sysv_ipc

from .cache import CycledCache
from .shared import SharedMemory


def create_memory_cache(size: int, name: str):
    if name.startswith('0x'):
        name = name[2:]
    key = int(name, 16)
    shm = sysv_ipc.SharedMemory(key=key, flags=sysv_ipc.IPC_CREAT, mode=MemoryCache.MODE, size=size)
    return MemoryCache(shm=shm)


class MemoryCache(CycledCache[sysv_ipc.SharedMemory]):

    MODE = 0o644

    def __init__(self, shm: sysv_ipc.SharedMemory):
        super().__init__(shm=shm, head_length=4)

    # Override
    def detach(self):
        self.shm.detach()

    # Override
    def remove(self):
        self.shm.remove()

    @property  # Override
    def buffer(self) -> bytes:
        return self.shm.read()

    @property  # Override
    def size(self) -> int:
        return self.shm.size

    # Override
    def _set(self, pos: int, value: int):
        data = bytearray(1)
        data[0] = value
        self.shm.write(data, offset=pos)

    # Override
    def _get(self, pos: int) -> int:
        data = self.shm.read(1, offset=pos)
        return data[0]

    # Override
    def _update(self, start: int, end: int, data: Union[bytes, bytearray]):
        assert start + len(data) == end, '%d + %d != %d' % (start, len(data), end)
        self.shm.write(data, offset=start)

    # Override
    def _slice(self, start: int, end: int) -> Union[bytes, bytearray]:
        return self.shm.read(end - start, offset=start)


class SharedMemoryCache(SharedMemory[sysv_ipc.SharedMemory]):

    def __init__(self, size: int, name: str):
        cache = create_memory_cache(size=size, name=name)
        super().__init__(cache=cache)

    @property
    def id(self) -> int:
        return self.cache.shm.id

    @property
    def key(self) -> int:
        return self.cache.shm.key

    @property
    def mode(self) -> int:
        return self.cache.shm.mode

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        cache = self.cache
        return '<%s id=%d key=0x%08x mode=%o>%s</%s "%s">' % (cname, self.id, self.key, self.mode, cache, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        cache = self.cache
        return '<%s id=%d key=0x%08x mode=%o>%s</%s "%s">' % (cname, self.id, self.key, self.mode, cache, cname, mod)
