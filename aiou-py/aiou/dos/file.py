# -*- coding: utf-8 -*-
#
#   Async File System
#
#                                Written in 2024 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Albert Moky
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
import json
import multiprocessing
from typing import Optional, Union, List, Dict

import aiofiles

from .path import Path


class BinaryAccess:

    async def read(self, path: str) -> Optional[bytes]:
        async with aiofiles.open(path, mode='rb') as file:
            return await file.read()

    async def write(self, data: bytes, path: str) -> int:
        async with aiofiles.open(path, mode='wb') as file:
            return await file.write(data)

    async def append(self, data: bytes, path: str) -> int:
        async with aiofiles.open(path, mode='ab') as file:
            return await file.write(data)


class LockedAccess(BinaryAccess):

    def __init__(self, lock):
        super().__init__()
        self.__lock = lock

    # Override
    async def read(self, path: str) -> Optional[bytes]:
        with self.__lock:
            return await super().read(path=path)

    # Override
    async def write(self, data: bytes, path: str) -> int:
        with self.__lock:
            return await super().write(data=data, path=path)

    # Override
    async def append(self, data: bytes, path: str) -> int:
        with self.__lock:
            return await super().append(data=data, path=path)


class SafelyAccess:

    def __init__(self, access: BinaryAccess):
        super().__init__()
        self.__dos = access

    async def read(self, path: str) -> Optional[bytes]:
        try:
            return await self.__dos.read(path=path)
        except Exception as error:
            print('[DOS] reading file error: %s, path=%s' % (error, path))

    async def write(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.write(data=data, path=path)
        except Exception as error:
            size = 0 if data is None else len(data)
            print('[DOS] writing file error: %s, %d byte(s), path=%s' % (error, size, path))

    async def append(self, data: bytes, path: str) -> int:
        try:
            return await self.__dos.append(data=data, path=path)
        except Exception as error:
            size = 0 if data is None else len(data)
            print('[DOS] appending file error: %s, %d byte(s), path=%s' % (error, size, path))


class FileHelper:

    LOCK_1 = asyncio.Lock()
    LOCK_2 = multiprocessing.Lock()

    lock = None
    # lock = LOCK_1
    # lock = LOCK_2

    safely = False

    @classmethod
    def get_access(cls):
        access = BinaryAccess()
        #
        #  locked to access
        #
        file_lock = cls.lock
        if file_lock is not None:
            access = LockedAccess(lock=file_lock)
        #
        #  try ... catch
        #
        if cls.safely:
            access = SafelyAccess(access=access)
        #
        #  OK
        #
        return access


class File:
    """ Binary File """

    def __init__(self, path: str):
        super().__init__()
        self.__path: str = path
        self.__data: Optional[bytes] = None

    @property
    def path(self) -> str:
        return self.__path

    async def read(self) -> Optional[bytes]:
        if self.__data is not None:
            # get data from cache
            return self.__data
        if not await Path.exists(path=self.__path):
            # file not found
            return None
        if not await Path.is_file(path=self.__path):
            # the path is not a file
            raise IOError('%s is not a file' % self.__path)
        # read
        dos = FileHelper.get_access()
        self.__data = await dos.read(path=self.__path)
        return self.__data

    async def write(self, data: bytes) -> bool:
        directory = Path.dir(path=self.__path)
        if not await Path.make_dirs(directory=directory):
            return False
        # write
        dos = FileHelper.get_access()
        cnt = await dos.write(data=data, path=self.__path)
        if len(data) != cnt:
            print('[DOS] failed to write file: %d/%d, %s' % (cnt, len(data), self.__path))
            return False
        # OK, update cache
        self.__data = data
        return True

    async def append(self, data: bytes) -> bool:
        if not await Path.exists(path=self.__path):
            # new file
            return await self.write(data)
        # append
        dos = FileHelper.get_access()
        cnt = await dos.append(data=data, path=self.__path)
        if len(data) != cnt:
            print('[DOS] failed to append file: %d/%d, %s' % (cnt, len(data), self.__path))
            return False
        # OK, erase cache for next update
        self.__data = None
        return True


class TextFile:

    def __init__(self, path: str):
        super().__init__()
        self.__file = File(path=path)
        self.__text: Optional[str] = None

    @property
    def path(self) -> str:
        return self.__file.path

    async def read(self, encoding: str = 'utf-8') -> Optional[str]:
        if encoding is None or len(encoding) == 0:
            encoding = 'utf-8'
        if self.__text is not None:
            # get data from cache
            return self.__text
        # 1. load from file
        data = await self.__file.read()
        if data is None:
            # file not found?
            return None
        # 2. decode text string
        text = data.decode(encoding)
        if text is None:
            raise ValueError('cannot convert with encoding: %s, data: %s' % (encoding, data))
        # 3. cache the result
        self.__text = text
        return text

    async def write(self, text: str, encoding: str = 'utf-8') -> bool:
        if encoding is None or len(encoding) == 0:
            encoding = 'utf-8'
        # 1. encode text string
        data = text.encode(encoding)
        if data is None:
            raise ValueError('cannot convert with encoding: %s, text: %s' % (encoding, text))
        # 2. save into file
        if await self.__file.write(data=data):
            # 3. update cache
            self.__text = text
            return True
        else:
            # error
            self.__text = None

    async def append(self, text: str, encoding: str = 'utf-8') -> bool:
        if encoding is None or len(encoding) == 0:
            encoding = 'utf-8'
        self.__text = None
        data = text.encode(encoding)
        return await self.__file.append(data)


class JSONFile:

    def __init__(self, path: str):
        super().__init__()
        self.__file = TextFile(path=path)
        self.__container: Union[Dict, List, None] = None

    @property
    def path(self) -> str:
        return self.__file.path

    async def read(self) -> Union[Dict, List, None]:
        if self.__container is not None:
            # get content from cache
            return self.__container
        # 1. load from text file
        text = await self.__file.read()
        if text is None:
            # file not found?
            return None
        # 2. convert text string to JSON object
        container = json.loads(text)
        if container is None:
            raise ValueError('cannot convert from JSON string: %s' % text)
        # 3. cache the result
        self.__container = container
        return container

    async def write(self, container: Union[Dict, List]) -> bool:
        # 1. convert JSON object to text string
        text = json.dumps(container)
        if text is None:
            raise ValueError('cannot convert to JSON string: %s' % container)
        # 2. save into text file
        if await self.__file.write(text=text):
            # 3. update cache
            self.__container = container
            return True
        else:
            # error
            self.__container = None
