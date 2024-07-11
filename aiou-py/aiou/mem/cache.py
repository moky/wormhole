# -*- coding: utf-8 -*-
#
#   Memory Cache
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

import time
from typing import TypeVar, Generic, Optional, Tuple, Set, Dict


"""
    Memory Cache
    ~~~~~~~~~~~~
    
    Cache data with key in local memory
"""


K = TypeVar('K')
V = TypeVar('V')


class CacheHolder(Generic[V]):
    """ Holder for caching value """

    def __init__(self, value: Optional[V], life_span: float, now: float = None):
        super().__init__()
        if now is None:
            now = time.time()
        else:
            assert now > 0, 'time error: %s' % str(now)
        self.__value = value
        self.__life_span = life_span
        self.__expired = now + life_span
        self.__deprecated = now + life_span * 2

    @property
    def value(self) -> Optional[V]:
        """ get cached value """
        return self.__value

    def update(self, value: V, now: float = None):
        """ update cached value and refresh expired times """
        if now is None:
            now = time.time()
        else:
            assert now > 0, 'time error: %s' % str(now)
        life_span = self.__life_span
        self.__value = value
        self.__expired = now + life_span
        self.__deprecated = now + life_span * 2

    def is_alive(self, now: float = None) -> bool:
        """ check whether this cache needs updating """
        if now is None:
            now = time.time()
        else:
            assert now > 0, 'time error: %s' % str(now)
        return now < self.__expired

    def is_deprecated(self, now: float = None) -> bool:
        """ check whether this cache can be purged """
        if now is None:
            now = time.time()
        else:
            assert now > 0, 'time error: %s' % str(now)
        return now > self.__deprecated

    def renewal(self, duration: float = 128, now: float = None):
        """ refresh expired times """
        if now is None:
            now = time.time()
        else:
            assert now > 0, 'time error: %s' % str(now)
        life_span = self.__life_span
        self.__deprecated = now + life_span * 2
        self.__expired = now + duration


class CachePool(Generic[K, V]):
    """ Pool for cache holders """

    def __init__(self):
        self.__holders: Dict[K, CacheHolder[V]] = {}  # key -> holder(value)

    def all_keys(self) -> Set[K]:
        """ get all cache keys """
        return set(self.__holders.keys())

    def update(self, key: K, holder: CacheHolder[V] = None,
               value: V = None, life_span: float = 3600, now: float = None) -> CacheHolder[V]:
        """ update: key -> holder(value) """
        if life_span is None:
            life_span = 3600
        if holder is None:
            holder = CacheHolder(value=value, life_span=life_span, now=now)
        self.__holders[key] = holder
        return holder

    def erase(self, key: K, now: float = None) -> Tuple[Optional[V], Optional[CacheHolder[V]]]:
        """ erase value holder with key """
        if now is None:
            self.__holders.pop(key, None)
            return None, None
        # get exists value before erasing
        value, holder = self.fetch(key=key, now=now)
        self.__holders.pop(key, None)
        return value, holder

    def fetch(self, key: K, now: float = None) -> Tuple[Optional[V], Optional[CacheHolder[V]]]:
        """ fetch value & holder with key """
        holder = self.__holders.get(key)
        if holder is None:
            # holder not found
            return None, None
        elif holder.is_alive(now=now):
            return holder.value, holder
        else:
            # holder expired
            return None, holder

    def purge(self, now: float = None) -> int:
        """ remove all expired cache holders """
        if now is None:
            now = time.time()
        else:
            assert now > 0, 'time error: %s' % str(now)
        count = 0
        keys = self.all_keys()
        for key in keys:
            holder = self.__holders.get(key)
            if holder is None or holder.is_deprecated(now=now):
                # remove expired holders
                self.__holders.pop(key, None)
                count += 1
        return count


class CacheManager:
    """ Manager for cache pools """

    def __init__(self):
        super().__init__()
        self.__pools: Dict[str, CachePool] = {}  # name -> pool

    def all_names(self) -> Set[K]:
        """ get names of all pools """
        return set(self.__pools.keys())

    def get_pool(self, name: str) -> CachePool[K, V]:
        """ get pool with name """
        pool = self.__pools.get(name)
        if pool is None:
            pool = CachePool()
            self.__pools[name] = pool
        return pool

    def remove_pool(self, name: str) -> Optional[CachePool[K, V]]:
        """ remove pool with name """
        return self.__pools.pop(name, None)

    def purge(self, now: float = None) -> int:
        """ purge all pools """
        if now is None:
            now = time.time()
        else:
            assert now > 0, 'time error: %s' % str(now)
        count = 0
        names = self.all_names()
        for name in names:
            pool = self.__pools.get(name)
            if pool is not None:
                count += pool.purge(now=now)
        return count
