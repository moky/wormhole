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
from typing import TypeVar, Generic, Optional, Set, MutableMapping

from .pair import Address


K = TypeVar('K')
V = TypeVar('V')


class KeyPairMap(Generic[K, V], ABC):

    @property
    def items(self) -> Set[V]:
        """ Get all mapped items """
        raise NotImplemented

    @abstractmethod
    def get(self, remote: Optional[K], local: Optional[K]) -> Optional[V]:
        """ Get item by key pair (remote, local) """
        raise NotImplemented

    @abstractmethod
    def set(self, remote: Optional[K], local: Optional[K], item: Optional[V]):
        """ Set item by key pair (remote, local) """
        raise NotImplemented

    @abstractmethod
    def remove(self, remote: Optional[K], local: Optional[K], item: Optional[V]) -> Optional[V]:
        """ Remove mapping item by key pair (remote, local) """
        raise NotImplemented


class WeakKeyPairMap(KeyPairMap[K, V], ABC):

    def __init__(self, default: K):
        super().__init__()
        self.__default = default  # default key
        self.__map: MutableMapping[K, MutableMapping[K, V]] = {}  # (K, K) => V

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
            item = table.get(key2)
            if item is not None:
                return item
            # take any Connection connected to remote
            return table.get(self.__default)
        else:
            # mapping: (remote, None) => Connection
            # mapping: (local, None) => Connection
            item = table.get(self.__default)
            if item is not None:
                # take the item with empty key2
                return item
            # take any Connection connected to remote / bound to local
            for name in table:
                item = table.get(name)
                if item is not None:
                    return item

    # Override
    def set(self, remote: Optional[K], local: Optional[K], item: Optional[V]):
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
            if item is not None:
                table[key2] = item
            else:
                table.pop(key2, None)
        elif item is not None:
            table = weakref.WeakValueDictionary()
            table[key2] = item
            self.__map[key1] = table

    # Override
    def remove(self, remote: Optional[K], local: Optional[K], item: Optional[V]) -> Optional[V]:
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
            # del (remote, local)
            # del (remote, None)
            # del (None, local)
            return table.pop(key2, None)


class HashKeyPairMap(WeakKeyPairMap[K, V]):

    def __init__(self, default: K):
        super().__init__(default=default)
        self.__items: Set[V] = set()

    @property
    def items(self) -> Set[V]:
        return set(self.__items)

    # Override
    def set(self, remote: Optional[K], local: Optional[K], item: Optional[V]):
        if item is not None:
            # the caller may create different values with same pair (remote, local)
            # so here we should try to remove it first to make sure it's clean
            self.__items.discard(item)
            # cache it
            self.__items.add(item)
        # create indexes
        super().set(remote=remote, local=local, item=item)

    # Override
    def remove(self, remote: Optional[K], local: Optional[K], item: Optional[V]) -> Optional[V]:
        # remove indexes
        old = super().remove(remote=remote, local=local, item=item)
        if old is not None:
            self.__items.discard(old)
            return old
        elif item is not None:
            self.__items.discard(item)
            return item


class AddressPairMap(HashKeyPairMap[Address, V]):

    AnyAddress = ('0.0.0.0', 0)

    def __init__(self):
        super().__init__(default=self.AnyAddress)
