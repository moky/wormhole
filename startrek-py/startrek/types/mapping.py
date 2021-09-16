# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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

import weakref
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Union, Set, Dict, Any

K = TypeVar('K')
V = TypeVar('V')


class KeyPairMap(Generic[K, V], ABC):

    @property
    def values(self) -> Set[V]:
        """ Get all mapped values """
        raise NotImplemented

    @abstractmethod
    def get(self, remote: Optional[K], local: Optional[K]) -> Optional[V]:
        """ Get value by key pair (remote, local) """
        raise NotImplemented

    @abstractmethod
    def put(self, remote: Optional[K], local: Optional[K], value: Optional[V]):
        """ Set value by key pair (remote, local) """
        raise NotImplemented

    @abstractmethod
    def remove(self, remote: Optional[K], local: Optional[K], value: Optional[V]) -> Optional[V]:
        """ Remove mapping value by key pair (remote, local) """
        raise NotImplemented


class WeakKeyPairMap(KeyPairMap[K, V], ABC):

    def __init__(self, default: K):
        super().__init__()
        self.__default = default
        self.__map: Dict[K, Union[Dict[K, V], Any]] = {}

    # Override
    def get(self, remote: Optional[K], local: Optional[K]) -> Optional[V]:
        if remote is None:
            assert local is not None, 'local & remote addresses should not empty at the same time'
            key1 = local
            key2 = None
        else:
            key1 = remote
            key2 = local
        table = self.__map.get(key1)
        if table is None:
            return None
        if key2 is not None:
            # mapping: (remote, local) => Connection
            return table.get(key2)
        # mapping: (remote, None) => Connection
        # mapping: (local, None) => Connection
        value = table.get(self.__default)
        if value is not None:
            # take the value with empty key2
            return value
        else:
            # take the first value if exists
            for item in table.values():
                return item

    # Override
    def put(self, remote: Optional[K], local: Optional[K], value: Optional[V]):
        # create indexes with key pair (remote, local)
        if remote is None:
            assert local is not None, 'local & remote addresses should not empty at the same time'
            key1 = local
            key2 = self.__default
        elif local is None:
            key1 = remote
            key2 = self.__default
        else:
            key1 = remote
            key2 = local
        table = self.__map.get(key1)
        if table is not None:
            if value is not None:
                table[key2] = value
            else:
                table.pop(key2, None)
        elif value is not None:
            table = weakref.WeakValueDictionary()
            table[key2] = value
            self.__map[key1] = table

    # Override
    def remove(self, remote: Optional[K], local: Optional[K], value: Optional[V]) -> Optional[V]:
        # remove indexes with key pair (remote, local)
        if remote is None:
            assert local is not None, 'local & remote addresses should not empty at the same time'
            key1 = local
            key2 = self.__default
        elif local is None:
            key1 = remote
            key2 = self.__default
        else:
            key1 = remote
            key2 = local
        table = self.__map.get(key1)
        if table is not None:
            # assert isinstance(table, dict)
            return table.pop(key2, None)


class HashKeyPairMap(WeakKeyPairMap[K, V]):

    def __init__(self, default: K):
        super().__init__(default=default)
        self.__values: Set[V] = set()

    @property
    def values(self) -> Set[V]:
        return set(self.__values)

    # Override
    def put(self, remote: Optional[K], local: Optional[K], value: Optional[V]):
        if value is not None:
            # the caller may create different values with same pair (remote, local)
            # so here we should try to remove it first to make sure it's clean
            self.__values.discard(value)
            # cache it
            self.__values.add(value)
        # create indexes
        super().put(remote=remote, local=local, value=value)

    # Override
    def remove(self, remote: Optional[K], local: Optional[K], value: Optional[V]) -> Optional[V]:
        # remove indexes
        old = super().remove(remote=remote, local=local, value=value)
        if old is not None:
            self.__values.discard(old)
        # clear cached value
        if value is not None and value is not old:
            self.__values.discard(value)
        if old is None:
            return value
        else:
            return old


class AddressPairMap(HashKeyPairMap[tuple, V]):

    AnyAddress = ('0.0.0.0', 0)

    def __init__(self):
        super().__init__(default=self.AnyAddress)
