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
import os
import tempfile
import threading
from abc import ABC, abstractmethod
from typing import Optional
from weakref import WeakValueDictionary

import aiofiles

from small.utils import final
from small.log import Logging
from small.lock import AsyncLock


def _fix_permissions(path: str, tmp: str):
    """ keep the original file mode for the new file, or a sane default """
    try:
        mode = os.stat(path).st_mode & 0o7777
    except OSError:
        mode = 0o644  # default
    try:
        os.chmod(tmp, mode)
    except OSError:
        pass


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
        # write to a temp file, then atomically replace the target,
        # so concurrent readers never observe a partial file
        def _write():
            directory = os.path.dirname(path)
            if not directory:
                directory = '.'
            fd, tmp = tempfile.mkstemp(prefix='.', suffix='.tmp', dir=directory)
            try:
                with os.fdopen(fd, 'wb') as file:
                    file.write(data)
                _fix_permissions(path=path, tmp=tmp)
                os.replace(tmp, path)
            except BaseException:
                try:
                    os.close(fd)   # fdopen may have failed before closing it
                except OSError:
                    pass
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                raise
            return len(data)
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
        # write to a temp file, then atomically replace the target,
        # so concurrent readers never observe a partial file
        directory = os.path.dirname(path)
        if not directory:
            directory = '.'
        fd, tmp = tempfile.mkstemp(prefix='.', suffix='.tmp', dir=directory)
        try:
            # aiofiles has no fdopen; it re-opens by path, so the reserved
            # fd is only used to create the empty temp file, then closed
            os.close(fd)
            async with aiofiles.open(tmp, mode='wb') as file:
                await file.write(data)
            _fix_permissions(path=path, tmp=tmp)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise
        return len(data)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        async with aiofiles.open(path, mode='ab') as file:
            return await file.write(data)


class LockedAccess(BinaryAccess):
    """ Lock for writing, by file path (read is lock-free).

        Write operations replace the file atomically, so readers always get
        a complete file without any lock; a per-path lock only serializes
        writers of the same file, preventing write/append races while
        different files stay fully parallel.
    """

    # path => lock (shared by all instances)
    #
    # Weak values: a lock is strongly referenced while being held (async with),
    # and gets garbage-collected right after it is released, so the map shrinks
    # automatically and never grows with long-lived/dynamic file paths.
    _locks = WeakValueDictionary()
    _guard = threading.Lock()   # guards the map only (micro-seconds)

    def __init__(self, access: BinaryAccess):
        super().__init__()
        self.__dos = access

    @classmethod
    def _get_lock(cls, path: str):
        with cls._guard:
            lock = cls._locks.get(path)
            if lock is None:
                lock = AsyncLock.create()
                cls._locks[path] = lock
            return lock

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        # no lock: the writer replaces the file atomically,
        # so we always read a complete file
        return await self.__dos.read(path=path)

    # Override
    async def write(self, data: bytes, path: str) -> int:
        lock = self._get_lock(path=path)
        async with lock:
            return await self.__dos.write(data=data, path=path)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        lock = self._get_lock(path=path)
        async with lock:
            return await self.__dos.append(data=data, path=path)


class SafelyAccess(BinaryAccess, Logging):

    def __init__(self, access: BinaryAccess):
        super().__init__()
        self.__dos = access

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        try:
            return await self.__dos.read(path=path)
        except OSError as error:
            self.error('[DOS] failed to read: %s, path=%s', error, path)
            return None

    # Override
    async def write(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.write(data=data, path=path)
        except OSError as error:
            self.error('[DOS] failed to write: %s, %d byte(s), path=%s', error, len(data), path)
            return -1

    # Override
    async def append(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.append(data=data, path=path)
        except OSError as error:
            self.error('[DOS] failed to append: %s, %d byte(s), path=%s', error, len(data), path)
            return -1


@final
class FileHelper:

    access: Optional[BinaryAccess] = None

    @classmethod
    def get_access(cls, synchronized: bool = True, safely: bool = True) -> BinaryAccess:
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
        #  per-file write locks (read is lock-free)
        #
        access = LockedAccess(access=access)
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
