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

    @abstractmethod
    async def write(self, data: bytes, path: str) -> int:
        raise NotImplemented

    @abstractmethod
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


class SyncLockedAccess(BinaryAccess):

    def __init__(self, lock, access: BinaryAccess):
        super().__init__()
        self.__lock = lock
        self.__dos = access

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        with self.__lock:
            return await self.__dos.read(path=path)

    # Override
    async def write(self, data: bytes, path: str) -> int:
        with self.__lock:
            return await self.__dos.write(data=data, path=path)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        with self.__lock:
            return await self.__dos.append(data=data, path=path)


class AsyncLockedAccess(BinaryAccess):

    def __init__(self, lock, access: BinaryAccess):
        super().__init__()
        self.__lock = lock
        self.__dos = access

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        async with self.__lock:
            return await self.__dos.read(path=path)

    # Override
    async def write(self, data: bytes, path: str) -> int:
        async with self.__lock:
            return await self.__dos.write(data=data, path=path)

    # Override
    async def append(self, data: bytes, path: str) -> int:
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
            print('[DOS] failed to read: %s, path=%s' % (error, path))
            return None

    # Override
    async def write(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.write(data=data, path=path)
        except Exception as error:
            size = 0 if data is None else len(data)
            print('[DOS] failed to write: %s, %d byte(s), path=%s' % (error, size, path))
            return -1

    # Override
    async def append(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.append(data=data, path=path)
        except Exception as error:
            size = 0 if data is None else len(data)
            print('[DOS] failed to append: %s, %d byte(s), path=%s' % (error, size, path))
            return -1


#
#   Factory
#


class LockFactory:

    # noinspection PyMethodMayBeStatic
    def create_lock(self, name: Optional[str]):
        """ get lock & sync flag """
        if name == 'asyncio':
            return asyncio.Lock(), False
        elif name == 'threading':
            return threading.Lock(), True
        elif name == 'multiprocessing':
            return multiprocessing.Lock(), True
        else:
            assert name is None, 'unknown lock: %s' % name
            return None, False


class FileHelper:

    access: Optional[BinaryAccess] = None

    lock_factory = LockFactory()

    @classmethod
    def get_lock(cls, name: Optional[str]):
        factory = cls.lock_factory
        return factory.create_lock(name=name)

    @classmethod
    def get_access(cls, synchronized: bool = True, lock_name: str = None, safely: bool = True) -> BinaryAccess:
        access = cls.access
        if access is not None:
            # already created
            return access
        #
        #  sync / async
        #
        if synchronized:
            access = SyncAccess()
        else:
            access = AsyncAccess()
        #
        #  locked access
        #
        lock, sync = cls.get_lock(name=lock_name)
        if lock is None:
            # no lock
            pass
        elif sync:
            access = SyncLockedAccess(lock=lock, access=access)
        else:
            access = AsyncLockedAccess(lock=lock, access=access)
        #
        #  try ... catch
        #
        if safely:
            access = SafelyAccess(access=access)
        #
        #  OK
        #
        cls.access = access
        return access

    #
    #   Binary Access
    #

    @classmethod
    async def read(cls, path: str) -> Optional[bytes]:
        dos = cls.get_access()
        return await dos.read(path=path)

    @classmethod
    async def write(cls, data: bytes, path: str) -> int:
        dos = cls.get_access()
        return await dos.write(data=data, path=path)

    @classmethod
    async def append(cls, data: bytes, path: str) -> int:
        dos = cls.get_access()
        return await dos.append(data=data, path=path)
