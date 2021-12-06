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


class MemoryCache(CycledCache):

    def __init__(self, shm: sysv_ipc.SharedMemory):
        self.__shm = shm
        super().__init__(buffer=None, head_length=4)

    @property  # Override
    def bounds(self) -> int:
        return self.__shm.size

    # Override
    def _set(self, pos: int, value: int):
        data = bytearray(1)
        data[0] = value
        self.__shm.write(data, offset=pos)

    # Override
    def _get(self, pos: int) -> int:
        data = self.__shm.read(1, offset=pos)
        return data[0]

    # Override
    def _update(self, start: int, end: int, data: Union[bytes, bytearray]):
        assert start + len(data) == end, '%d + %d != %d' % (start, len(data), end)
        self.__shm.write(data, offset=start)

    # Override
    def _slice(self, start: int, end: int) -> Union[bytes, bytearray]:
        return self.__shm.read(end - start, offset=start)


class SharedMemoryCache(SharedMemory):

    MODE = 0o644

    def __init__(self, size: int, name: str, create: bool = True):
        if name.startswith('0x'):
            name = name[2:]
        key = int(name, 16)
        if create:
            flags = sysv_ipc.IPC_CREAT
        else:
            flags = sysv_ipc.IPC_PRIVATE
        shm = sysv_ipc.SharedMemory(key=key, flags=flags, mode=self.MODE, size=size)
        cache = MemoryCache(shm=shm)
        super().__init__(cache=cache)
        self.__shm = shm

    @property
    def shm(self) -> sysv_ipc.SharedMemory:
        return self.__shm

    @property  # Override
    def buffer(self) -> bytes:
        return self.__shm.read()

    # Override
    def detach(self):
        self.__shm.detach()

    # Override
    def remove(self):
        self.__shm.remove()

    @property
    def id(self) -> int:
        return self.__shm.id

    @property
    def key(self) -> int:
        return self.__shm.key

    @property
    def mode(self) -> int:
        return self.__shm.mode

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s %d|0x%08x mode=%o size=%d capacity=%d available=%d>\n%s\n</%s module="%s">' %\
               (cname, self.id, self.key, self.mode, self.size, self.capacity, self.available, self.buffer, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s %d|0x%08x mode=%o size=%d capacity=%d available=%d>\n%s\n</%s module="%s">' %\
               (cname, self.id, self.key, self.mode, self.size, self.capacity, self.available, self.buffer, cname, mod)
