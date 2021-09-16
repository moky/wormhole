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

from typing import TypeVar, Generic


K = TypeVar('K')
V = TypeVar('V')


class Pair(Generic[K, V]):

    def __init__(self, key: K, value: V):
        super().__init__()
        self.__key = key
        self.__value = value

    @property
    def key(self) -> K:
        return self.__key

    @property
    def value(self) -> V:
        return self.__value

    def __str__(self) -> str:
        return '%s=%s' % (self.__key, self.__value)

    def __repr__(self) -> str:
        return '%s=%s' % (self.__key, self.__value)

    def __hash__(self):
        # name's hashCode is multiplied by an arbitrary prime number (13)
        # in order to make sure there is a difference in the hashCode between
        # these two parameters:
        #  name: a  value: aa
        #  name: aa value: a
        if self.__value is None:
            return hash(self.__key) * 13
        else:
            return hash(self.__key) * 13 + hash(self.__value)

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(other, Pair):
            return self.__key == other.__key and self.__value == other.__value

    def __ne__(self, other):
        if self is other:
            return False
        elif isinstance(other, Pair):
            return self.__key != other.__key or self.__value != other.__value
        else:
            return True
