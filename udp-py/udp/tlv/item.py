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

from typing import Optional

from .data import Data, IntData
from .data import bytes_to_int


"""
       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |         Type                  |            Length             |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Value (variable)                ....
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""


class Tag(Data):

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2:
            return None
        elif data_len > 2:
            data = data[:2]
        return cls(data=data)


class Length(IntData):

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: bytes, tag: Tag):
        data_len = len(data)
        if data_len < 2:
            return None
        elif data_len > 2:
            data = data[:2]
        value = bytes_to_int(data=data)
        return cls(data=data, value=value)


class Value(Data):

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: bytes, tag: Tag, length: Length=None):
        if length is None or length.value == 0:
            return None
        else:
            length = length.value
        data_len = len(data)
        if data_len < length:
            return None
        elif data_len > length:
            data = data[:length]
        return cls(data=data)


class TagLengthValue(Data):

    def __init__(self, data: bytes, tag: Tag, value: Optional[Value]):
        super().__init__(data=data)
        self.__tag = tag
        self.__value = value

    @property
    def tag(self) -> Tag:
        return self.__tag

    @property
    def value(self) -> Optional[Value]:
        return self.__value

    @classmethod
    def parse_all(cls, data: bytes) -> list:
        array = []
        remaining = len(data)
        while remaining > 0:
            item = cls.parse(data=data)
            if item is None:
                # data error
                break
            array.append(item)
            # next item
            pos = len(item.data)
            data = data[pos:]
            remaining -= pos
        return array

    @classmethod
    def parse(cls, data: bytes):
        # get tag
        tag = cls.parse_tag(data=data)
        if tag is None:
            return None
        offset = len(tag.data)
        # get length
        length = cls.parse_length(data=data[offset:], tag=tag)
        if length is not None:
            offset += len(length.data)
        # get value
        value = cls.parse_value(data=data[offset:], tag=tag, length=length)
        if value is not None:
            offset += len(value.data)
        # create
        if offset < len(data):
            return cls._create(data=data[:offset], tag=tag, value=value)
        else:
            assert offset == len(data), 'offset error: %d > %d' % (offset, len(data))
            return cls._create(data=data, tag=tag, value=value)

    @classmethod
    def _create(cls, data: bytes, tag: Tag, value: Value=None):
        return cls(data=data, tag=tag, value=value)

    @classmethod
    def parse_tag(cls, data: bytes) -> Optional[Tag]:
        return Tag.parse(data=data)

    @classmethod
    def parse_length(cls, data: bytes, tag: Tag) -> Optional[Length]:
        return Length.parse(data=data, tag=tag)

    @classmethod
    def parse_value(cls, data: bytes, tag: Tag, length: Length=None) -> Optional[Value]:
        return Value.parse(data=data, tag=tag, length=length)
