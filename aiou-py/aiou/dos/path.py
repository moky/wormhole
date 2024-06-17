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

import os
import sys

from aiofiles import os as async_os


class Path:
    """
        Paths for main script
        ~~~~~~~~~~~~~~~~~~~~~
        #! /usr/bin/env python3
        import os
        import sys
        path = os.path.abspath(__file__)
        path = os.path.dirname(path)
        path = os.path.dirname(path)
        sys.path.insert(0, path)
    """

    @classmethod
    def dir(cls, path: str) -> str:
        # '/home/User/Documents' -> '/home/User'
        # '/home/User/Documents/file.txt' -> '/home/User/Documents'
        return os.path.dirname(path)

    @classmethod
    def abs(cls, path: str) -> str:
        # 'file.txt' -> '/home/User/Documents/file.txt'
        return os.path.abspath(path)

    @classmethod
    def add(cls, path: str):
        """ add system path """
        sys.path.insert(0, path)

    """
        Path Utils
        ~~~~~~~~~~
    """

    @classmethod
    def join(cls, parent: str, *children: str) -> str:
        # 'parent/child_1/child_2'
        return os.path.join(parent, *children)

    @classmethod
    async def is_dir(cls, path: str) -> bool:
        return os.path.isdir(path)

    @classmethod
    async def is_file(cls, path: str) -> bool:
        return os.path.isfile(path)

    @classmethod
    async def exists(cls, path: str) -> bool:
        return os.path.exists(path)

    @classmethod
    async def remove(cls, path: str) -> bool:
        if os.path.exists(path):
            # os.remove(path)
            await async_os.remove(path)
            return True

    @classmethod
    async def make_dirs(cls, directory: str) -> bool:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            # await async_os.makedirs(directory, exist_ok=True)
            return True
        elif os.path.isdir(directory):
            # directory exists
            return True
        else:
            raise IOError('%s exists but is not a directory!' % directory)
