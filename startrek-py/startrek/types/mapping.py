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
from typing import TypeVar, Generic, Optional, Set, Iterable, MutableMapping

from .pair import SocketAddress


K = TypeVar('K')
V = TypeVar('V')


class PairMap(Generic[K, V], ABC):

    @property
    @abstractmethod
    def items(self) -> Iterable[V]:
        """ Get all mapped items """
        raise NotImplemented

    @abstractmethod
    def get(self, remote: Optional[K], local: Optional[K]) -> Optional[V]:
        """ Get item by key pair (remote, local) """
        raise NotImplemented

    @abstractmethod
    def set(self, item: Optional[V], remote: Optional[K], local: Optional[K]) -> Optional[V]:
        """ Set item by key pair (remote, local) """
        raise NotImplemented

    @abstractmethod
    def remove(self, item: Optional[V], remote: Optional[K], local: Optional[K]) -> Optional[V]:
        """ Remove mapping item by key pair (remote, local) """
        raise NotImplemented


# noinspection PyAbstractClass
class AbstractPairMap(PairMap[K, V], ABC):

    def __init__(self, default: K):
        super().__init__()
        self.__default = default  # default key
        self.__map: MutableMapping[K, MutableMapping[K, V]] = {}  # (K, K) => V

    # @property  # Override
    # def items(self) -> Iterable[V]:
    #     # Caveat: the iterator will keep a strong reference to
    #     # `item` in WeakSet until it is resumed or closed.
    #     return self.__map.items()

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
    def set(self, item: Optional[V], remote: Optional[K], local: Optional[K]) -> Optional[V]:
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
                old = table.get(key2)
                table[key2] = item
                return old
            else:
                return table.pop(key2, None)
        elif item is not None:
            table = weakref.WeakValueDictionary()
            table[key2] = item
            self.__map[key1] = table

    # Override
    def remove(self, item: Optional[V], remote: Optional[K], local: Optional[K]) -> Optional[V]:
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
        if table is None:
            return item
        old = table.pop(key2, None)
        if len(table) == 0:
            self.__map.pop(key1, None)
        return item if old is None else old


class HashPairMap(AbstractPairMap[K, V]):

    def __init__(self, default: K):
        super().__init__(default=default)
        self.__items: Set[V] = set()

    @property  # Override
    def items(self) -> Iterable[V]:
        return self.__items.copy()

    # Override
    def set(self, item: Optional[V], remote: Optional[K], local: Optional[K]) -> Optional[V]:
        if item is not None:
            # the caller may create different values with same pair (remote, local)
            # so here we should try to remove it first to make sure it's clean
            self.__items.discard(item)
            # cache it
            self.__items.add(item)
        # create indexes
        old = super().set(item=item, remote=remote, local=local)
        # clear replaced value
        if old is not None and old != item:
            self.__items.discard(old)
        return old

    # Override
    def remove(self, item: Optional[V], remote: Optional[K], local: Optional[K]) -> Optional[V]:
        # remove indexes
        old = super().remove(item=item, remote=remote, local=local)
        if old is not None:
            self.__items.discard(old)
            # return old
        if item is not None and item != old:
            self.__items.discard(item)
            # return item
        return item if old is None else old


class AddressPairMap(HashPairMap[SocketAddress, V]):

    AnyAddress = ('0.0.0.0', 0)

    def __init__(self):
        super().__init__(default=self.AnyAddress)
