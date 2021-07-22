# -*- coding: utf-8 -*-
#
#   TLV: Tag Length Value
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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

from abc import abstractmethod
from typing import Generic, Union, Optional, List

from udp.ba import ByteArray, Data

from .tag import T, TagParser
from .length import L, LengthParser
from .value import V, ValueParser
from .entry import E, Entry, EntryParser


class Parser(EntryParser, Generic[E, T, L, V]):
    """ TLV Parser """

    @abstractmethod
    @property
    def tag_parser(self) -> TagParser[T]:
        """ get Tag Parser """
        raise NotImplemented

    @abstractmethod
    @property
    def length_parser(self) -> LengthParser[T, L]:
        """ get Length Parser """
        raise NotImplemented

    @abstractmethod
    @property
    def value_parser(self) -> ValueParser[T, L, V]:
        """ get Value Parser """
        raise NotImplemented

    @abstractmethod
    def create_entry(self, data: ByteArray, tag: T, length: L, value: V) -> E:
        """ Create TLV triad """
        raise NotImplemented

    def parse_entry(self, data: ByteArray) -> Optional[E]:
        # 1. get Tag field
        tag = self.tag_parser.parse_tag(data=data)
        if tag is None:
            return None
        offset = tag.size
        # 2. get Length field
        length = self.length_parser.parse_length(data=data.slice(start=offset), tag=tag)
        if length is None:
            # if length not defined, use the rest data as value
            value_length = data.size - offset
        else:
            value_length = length.value
            offset += length.size
        # 3. get value field
        end = offset + value_length
        value = self.value_parser.parse_value(data=data.slice(start=offset, end=end), tag=tag, length=length)
        # OK
        data = data.slice(start=0, end=end)
        return self.create_entry(data=data, tag=tag, length=length, value=value)

    def parse_entries(self, data: ByteArray) -> List[E]:
        entries = []
        while data.size > 0:
            entry = self.parse_entry(data=data)
            if entry is None:
                # data error
                break
            entries.append(entry)
            # next entry
            data = data.slice(start=entry.size)
        return entries


class Triad(Data, Entry, Generic[T, L, V]):
    """ TLV Entry """

    def __init__(self, data: Union[bytes, bytearray, ByteArray], tag: T, length: L, value: V):
        super().__init__(data=data)
        self.__tag = tag
        self.__length = length
        self.__value = value

    @property
    def tag(self) -> T:
        return self.__tag

    @property
    def length(self) -> L:
        return self.__length

    @property
    def value(self) -> V:
        return self.__value

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '/* %s */ %s: "%s"' % (clazz, self.tag, self.value)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '/* %s */ %s: "%s"' % (clazz, self.tag, self.value)
