# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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


class Type(Data):

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
    def parse(cls, data: bytes, t: Type):
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
    def parse(cls, data: bytes, t: Type, length: Length=None):
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


class TLV(Data):

    def __init__(self, data: bytes, t: Type, v: Optional[Value]):
        super().__init__(data=data)
        self.__type = t
        self.__value = v

    @property
    def type(self) -> Type:
        return self.__type

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
        # get type
        _type = cls.parse_type(data=data)
        if _type is None:
            return None
        offset = len(_type.data)
        # get length
        _len = cls.parse_length(data=data[offset:], t=_type)
        if _len is not None:
            offset += len(_len.data)
        # get value
        _value = cls.parse_value(data=data[offset:], t=_type, length=_len)
        if _value is not None:
            offset += len(_value.data)
        # create
        if offset < len(data):
            return cls(data=data[:offset], t=_type, v=_value)
        else:
            assert offset == len(data), 'offset error: %d > %d' % (offset, len(data))
            return cls(data=data, t=_type, v=_value)

    @classmethod
    def parse_type(cls, data: bytes) -> Optional[Type]:
        return Type.parse(data=data)

    @classmethod
    def parse_length(cls, data: bytes, t: Type) -> Optional[Length]:
        return Length.parse(data=data, t=t)

    @classmethod
    def parse_value(cls, data: bytes, t: Type, length: Length=None) -> Optional[Value]:
        return Value.parse(data=data, t=t, length=length)
