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

from typing import Optional, Dict

from aioredis import Redis, ConnectionPool


class RedisConnector:
    """ Connection Pool for Redis """

    def __init__(self, host: str = 'localhost', port: int = 6379, username: str = None, password: str = None):
        super().__init__()
        self.__host = host
        self.__port = port
        self.__username = username
        self.__password = password
        # pools
        self.__dbs: Dict[int, Redis] = {
            # 0 - default
            # 1
            # 2
            # 3
            # 4
            # 5
            # 6
            # 7
            # 8
            # 9
            # ...
        }

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port

    @property
    def username(self) -> Optional[str]:
        return self.__username

    @property
    def password(self) -> Optional[str]:
        return self.__password

    def get_redis(self, db: int) -> Redis:
        redis = self.__dbs.get(db)
        if redis is None:
            redis = create_redis(username=self.username, password=self.password,
                                 host=self.host, port=self.port, db=db)
            self.__dbs[db] = redis
        return redis


#
#   Creation
#
def create_redis(username: Optional[str], password: Optional[str],
                 host: str, port: int, db: int) -> Redis:
    pool = create_redis_pool(username=username, password=password, host=host, port=port, db=db)
    return Redis(connection_pool=pool, encoding='utf-8', decode_responses=False)


def create_redis_pool(username: Optional[str], password: Optional[str],
                      host: str, port: int, db: int) -> ConnectionPool:
    url = build_redis_url(username=username, password=password, host=host, port=port, db=db)
    return ConnectionPool.from_url(url=url)


def build_redis_url(username: Optional[str], password: Optional[str],
                    host: str, port: int, db: int) -> str:
    # redis://[[username]:[password]]@localhost:6379/0
    if password is not None:
        assert username is not None, 'Redis params error: "%s" (%s:%d)' % (password, host, port)
        return 'redis://%s:%s@%s:%d/%d' % (username, password, host, port, db)
    elif username is not None:
        return 'redis://%s@%s:%d/%d' % (username, host, port, db)
    else:
        return 'redis://%s:%d/%d' % (host, port, db)
