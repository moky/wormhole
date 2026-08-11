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
# import multiprocessing
# import threading
from abc import ABC, abstractmethod
from typing import Optional

import aiofiles


try:
    from typing import final
except ImportError:
    from typing_extensions import final


class BinaryAccess(ABC):

    @abstractmethod
    async def read(self, path: str) -> Optional[bytes]:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.read()'
        )

    @abstractmethod
    async def write(self, data: bytes, path: str) -> int:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.write()'
        )

    @abstractmethod
    async def append(self, data: bytes, path: str) -> int:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.append()'
        )


class SyncAccess(BinaryAccess):

    # noinspection PyMethodMayBeStatic
    async def _run_sync(self, func):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func)

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        def _read():
            with open(path, mode='rb') as file:
                return file.read()
        return await self._run_sync(_read)

    # Override
    async def write(self, data: bytes, path: str) -> int:
        def _write():
            with open(path, mode='wb') as file:
                return file.write(data)
        return await self._run_sync(_write)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        def _append():
            with open(path, mode='ab') as file:
                return file.write(data)
        return await self._run_sync(_append)


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
        except OSError as error:
            print('[DOS] failed to read: %s, path=%s' % (error, path))
            return None

    # Override
    async def write(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.write(data=data, path=path)
        except OSError as error:
            print('[DOS] failed to write: %s, %d byte(s), path=%s' % (error, len(data), path))
            return -1

    # Override
    async def append(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.append(data=data, path=path)
        except OSError as error:
            print('[DOS] failed to append: %s, %d byte(s), path=%s' % (error, len(data), path))
            return -1


#
#   Factory
#


class LockFactory:

    # noinspection PyMethodMayBeStatic
    def create_lock(self, name: Optional[str]):
        """ get lock & sync flag """
        if name == 'asyncio':
            return asyncio.Lock()
        # elif name == 'threading':
        #     return threading.Lock()
        # elif name == 'multiprocessing':
        #     return multiprocessing.Lock()
        else:
            assert name is None, 'unknown lock: %s' % name
            return None


@final
class FileHelper:

    access: Optional[BinaryAccess] = None

    lock_factory = LockFactory()

    @classmethod
    def get_lock(cls, name: Optional[str]):
        factory = cls.lock_factory
        return factory.create_lock(name=name)

    @classmethod
    def get_access(cls, synchronized: bool = True, lock_name: str = 'asyncio', safely: bool = True) -> BinaryAccess:
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
        lock = cls.get_lock(name=lock_name)
        if lock is not None:
            access = LockedAccess(lock=lock, access=access)
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
