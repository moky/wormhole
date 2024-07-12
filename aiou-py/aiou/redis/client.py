# -*- coding: utf-8 -*-
#
#   Async Redis
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

from typing import Optional, Iterable, Tuple, List, Dict

from redis import Redis


class RedisConnector:
    """ Connection Pool for Redis """

    def __init__(self, host: str = 'localhost', port: int = 6379, username: str = None, password: str = None):
        super().__init__()
        self.__host = 'localhost' if host is None else host
        self.__port = 6379 if port is None else port
        self.__username = username
        self.__password = password
        # connection pool
        self.__dbs: Dict[int, Redis] = {}

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

    def connect(self, db: int) -> Optional[Redis]:
        if db < 0:  # or db > 16:
            return None
        redis = self.__dbs.get(db)
        if redis is None:
            self.__dbs[db] = redis = self._create_redis(db=db)
        return redis

    def _create_redis(self, db: int) -> Redis:
        return Redis(host=self.host, port=self.port,
                     username=self.username, password=self.password,
                     db=db,
                     encoding='utf-8', decode_responses=False)


class RedisClient:
    """ Redis Wrapper """

    def __init__(self, connector: Optional[RedisConnector]):
        super().__init__()
        self.__connector = connector

    @property  # protected
    def connector(self) -> Optional[RedisConnector]:
        """ connection pool """
        return self.__connector

    @property  # protected
    def redis(self) -> Optional[Redis]:
        """ override to get redis by db/table name """
        connector = self.connector
        if connector is not None:
            return connector.connect(db=0)

    #
    #   Key -> Value
    #

    async def set(self, name: str, value: bytes, expires: Optional[int] = None):
        """ Set value with name """
        redis = self.redis
        if redis is None:
            return False
        redis.set(name=name, value=value, ex=expires)
        return True

    async def get(self, name: str) -> Optional[bytes]:
        """ Get value with name """
        redis = self.redis
        if redis is None:
            return None
        return redis.get(name=name)

    async def exists(self, *names) -> bool:
        """ Check whether value exists with name """
        redis = self.redis
        if redis is None:
            return False
        return redis.exists(*names)

    async def delete(self, *names):
        """ Remove value with name """
        redis = self.redis
        if redis is None:
            return False
        redis.delete(*names)
        return True

    async def expire(self, name: str, time: int) -> bool:
        """ Update expired time with name """
        redis = self.redis
        if redis is None:
            return False
        redis.expire(name=name, time=time)
        return True

    async def scan(self, cursor: int, match: str, count: int) -> Tuple[int, Optional[List[bytes]]]:
        """ Scan key names, return next cursor and partial results """
        redis = self.redis
        if redis is None:
            return 0, None
        return redis.scan(cursor=cursor, match=match, count=count)

    #
    #   Hash Mapping
    #

    async def hset(self, name: str, key: str, value: bytes):
        """ Set a value into a hash table with name & key """
        redis = self.redis
        if redis is None:
            return False
        redis.hset(name=name, key=key, value=value)
        return True

    async def hget(self, name: str, key: str) -> Optional[bytes]:
        """ Get value from the hash table with name & key """
        redis = self.redis
        if redis is None:
            return None
        return redis.hget(name=name, key=key)

    async def hgetall(self, name: str) -> Optional[Dict[bytes, bytes]]:
        """ Get all items from the hash table with name """
        redis = self.redis
        if redis is None:
            return None
        return redis.hgetall(name=name)

    async def hkeys(self, name: str) -> Iterable[str]:
        """ Return the list of keys within hash name """
        redis = self.redis
        if redis is None:
            return []
        keys = redis.hkeys(name=name)
        return [] if keys is None else keys

    async def hdel(self, name: str, key: str):
        """ Delete value from hash table with name & key """
        redis = self.redis
        if redis is None:
            return False
        redis.hdel(name, key)
        return True

    #
    #   Hash Set
    #

    async def sadd(self, name: str, *values):
        """ Add values into a hash set with name """
        redis = self.redis
        if redis is None:
            return False
        redis.sadd(name, *values)
        return True

    async def spop(self, name: str, count: Optional[int] = None):
        """ Remove and return a random member from the hash set with name """
        redis = self.redis
        if redis is None:
            return None
        return redis.spop(name=name, count=count)

    async def srem(self, name: str, *values):
        """ Remove values from the hash set with name """
        redis = self.redis
        if redis is None:
            return False
        redis.srem(name, *values)
        return True

    async def smembers(self, name: str) -> Iterable[bytes]:
        """ Get all items of the hash set with name """
        redis = self.redis
        if redis is None:
            return set()
        members = redis.smembers(name=name)
        return set() if members is None else members

    #
    #   Ordered Set
    #

    async def zadd(self, name: str, mapping: dict):
        """ Add value with score into an ordered set with name """
        redis = self.redis
        if redis is None:
            return False
        redis.zadd(name=name, mapping=mapping)
        return True

    async def zrem(self, name: str, *values):
        """ Remove values from the ordered set with name """
        redis = self.redis
        if redis is None:
            return False
        redis.zrem(name, *values)
        return True

    async def zremrangebyscore(self, name: str, min_score: int, max_score: int):
        """ Remove items with score range [min, max] """
        redis = self.redis
        if redis is None:
            return False
        redis.zremrangebyscore(name=name, min=min_score, max=max_score)
        return True

    async def zrange(self, name: str, start: int = 0, end: int = -1, desc: bool = False) -> List[bytes]:
        """ Get items with range [start, end] """
        redis = self.redis
        if redis is None:
            return []
        items = redis.zrange(name=name, start=start, end=end, desc=desc)
        return [] if items is None else items

    async def zcard(self, name: str) -> int:
        """ Get length of the ordered set with name """
        redis = self.redis
        if redis is None:
            return 0
        return redis.zcard(name=name)
