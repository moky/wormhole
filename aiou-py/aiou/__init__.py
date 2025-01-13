# -*- coding: utf-8 -*-
#
#   AIOU: Async I/O Utils
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

from .dos import Path
from .dos import File, TextFile, JSONFile
from .dos import SyncAccess, AsyncAccess, LockedAccess, SafelyAccess

from .redis import Redis
from .redis import RedisConnector, RedisClient

from .http import HttpResponse
from .http import HttpSession
from .http import HttpClient, CachedClient

from .mem import CacheHolder, CachePool, CacheManager


name = "AIOU"

__author__ = 'Albert Moky'


__all__ = [

    'Path',
    'File', 'TextFile', 'JSONFile',
    'SyncAccess', 'AsyncAccess', 'LockedAccess', 'SafelyAccess',

    'Redis',
    'RedisConnector', 'RedisClient',

    'HttpResponse',
    'HttpSession',
    'HttpClient', 'CachedClient',

    'CacheHolder',
    'CachePool',
    'CacheManager',

]
