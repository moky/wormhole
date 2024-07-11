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

from aioredis import Redis

from .dos import Path
from .dos import File, TextFile, JSONFile

from .redis import RedisConnector, RedisClient

from .http import HttpResponse
from .http import HttpSession
from .http import HttpClient, CachedClient


name = "AIOU"

__author__ = 'Albert Moky'


__all__ = [

    'Path',
    'File', 'TextFile', 'JSONFile',

    'Redis',
    'RedisConnector', 'RedisClient',

    'HttpResponse',
    'HttpSession',
    'HttpClient', 'CachedClient',

]


"""
    Patch 1
    ~~~~~~~
    TypeError: Instance and class checks can only be used with @runtime_checkable protocols
    
    
    python3.7/site-packages/aioredis/connection.py:572
    
        ConnectCallbackProtocol._is_runtime_protocol = True
        AsyncConnectCallbackProtocol._is_runtime_protocol = True
   
   
    python3.7/site-packages/aioredis/client.py:638
    
        ResponseCallbackProtocol._is_runtime_protocol = True
        AsyncResponseCallbackProtocol._is_runtime_protocol = True


    python3.7/site-packages/aioredis/client.py:4301

        PubsubWorkerExceptionHandler._is_runtime_protocol = True
        AsyncPubsubWorkerExceptionHandler._is_runtime_protocol = True

"""

"""
    Patch 2
    ~~~~~~~
    TypeError: Plain typing.NoReturn is not valid as type argument
    
    
    python3.7/site-packages/aioredis/lock.py:6
    
        NoReturn = None
        
        
    python3.7/site-packages/aioredis/client.py:30
    
        NoReturn = None
    
"""
