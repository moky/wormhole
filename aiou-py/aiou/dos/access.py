# -*- coding: utf-8 -*-
#
#   Async File System
#
#                                Written in 2025 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2025 Albert Moky
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

import asyncio
import multiprocessing
import threading
from abc import ABC, abstractmethod
from typing import Optional

import aiofiles


class BinaryAccess(ABC):

    @abstractmethod
    async def read(self, path: str) -> Optional[bytes]:
        raise NotImplemented

    async def write(self, data: bytes, path: str) -> int:
        raise NotImplemented

    async def append(self, data: bytes, path: str) -> int:
        raise NotImplemented


class SyncAccess(BinaryAccess):

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        with open(path, mode='rb') as file:
            return file.read()

    # Override
    async def write(self, data: bytes, path: str) -> int:
        with open(path, mode='wb') as file:
            return file.write(data)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        with open(path, mode='ab') as file:
            return file.write(data)


class AsyncAccess(BinaryAccess):

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        async with aiofiles.open(path, mode='rb') as file:
            return await file.read()

    # Override
    async def write(self, data: bytes, path: str) -> int:
        async with aiofiles.open(path, mode='wb') as file:
            return await file.write(data)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        async with aiofiles.open(path, mode='ab') as file:
            return await file.write(data)


class LockedAccess(BinaryAccess):

    def __init__(self, access: BinaryAccess, lock, sync: bool = False):
        super().__init__()
        self.__dos = access
        self.__lock = lock
        self.__sync = sync

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        if self.__sync:
            with self.__lock:
                return await self.__dos.read(path=path)
        else:
            async with self.__lock:
                return await self.__dos.read(path=path)

    # Override
    async def write(self, data: bytes, path: str) -> int:
        if self.__sync:
            with self.__lock:
                return await self.__dos.write(data=data, path=path)
        else:
            async with self.__lock:
                return await self.__dos.write(data=data, path=path)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        if self.__sync:
            with self.__lock:
                return await self.__dos.append(data=data, path=path)
        else:
            async with self.__lock:
                return await self.__dos.append(data=data, path=path)


class SafelyAccess(BinaryAccess):

    def __init__(self, access: BinaryAccess):
        super().__init__()
        self.__dos = access

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        try:
            return await self.__dos.read(path=path)
        except Exception as error:
            print('[DOS] reading file error: %s, path=%s' % (error, path))

    # Override
    async def write(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.write(data=data, path=path)
        except Exception as error:
            size = 0 if data is None else len(data)
            print('[DOS] writing file error: %s, %d byte(s), path=%s' % (error, size, path))

    # Override
    async def append(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.append(data=data, path=path)
        except Exception as error:
            size = 0 if data is None else len(data)
            print('[DOS] appending file error: %s, %d byte(s), path=%s' % (error, size, path))


class FileHelper:

    locks = {
        'asyncio': (asyncio.Lock(), False),
        'threading': (threading.Lock(), True),
        'multiprocessing': (multiprocessing.Lock(), True),
    }

    lock_name = None
    # lock_name = 'asyncio'
    # lock_name = 'threading'
    # lock_name = 'multiprocessing'

    synchronized = True
    safely = True

    @classmethod
    def get_lock(cls, name: Optional[str]):
        if name is None:
            return None, False
        # get lock + sync
        pair = cls.locks.get(name)
        if pair is None:
            return None, False
        else:
            return pair

    @classmethod
    def get_access(cls):
        #
        #   Sync / Async
        #
        if cls.synchronized:
            access = SyncAccess()
        else:
            access = AsyncAccess()
        #
        #  locked to access
        #
        lock, sync = cls.get_lock(name=cls.lock_name)
        if lock is not None:
            access = LockedAccess(access=access, lock=lock, sync=sync)
        #
        #  try ... catch
        #
        if cls.safely:
            access = SafelyAccess(access=access)
        #
        #  OK
        #
        return access
