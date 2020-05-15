# -*- coding: utf-8 -*-
#
#   STUN: Session Traversal Utilities for NAT
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

import binascii
import random
from typing import Optional


def hex_decode(string: str) -> bytes:
    return binascii.a2b_hex(string)


# noinspection PyUnusedLocal
def random_bytes(length: int) -> bytes:
    r = range(length << 1)
    a = ''.join([random.choice('0123456789ABCDEF') for i in r])
    return hex_decode(a)
    # return bytes(numpy.random.bytes(length))


def bytes_to_int(data: bytes, byteorder: str='big', signed: bool=False) -> int:
    return int.from_bytes(bytes=data, byteorder=byteorder, signed=signed)


def int_to_bytes(value: int, length: int, byteorder: str='big', signed: bool=False) -> bytes:
    return value.to_bytes(length=length, byteorder=byteorder, signed=signed)


def uint8_to_bytes(value: int, byteorder: str='big') -> bytes:
    return int_to_bytes(value=value, length=1, byteorder=byteorder)


def uint16_to_bytes(value: int, byteorder: str='big') -> bytes:
    return int_to_bytes(value=value, length=2, byteorder=byteorder)


def uint32_to_bytes(value: int, byteorder: str='big') -> bytes:
    return int_to_bytes(value=value, length=4, byteorder=byteorder)


class Data:
    """
        Data in bytes
    """

    def __init__(self, data: bytes):
        super().__init__()
        self.__data = data

    def __eq__(self, other) -> bool:
        if isinstance(other, Data):
            return self.data == other.data
        if isinstance(other, bytes):
            return self.data == other

    def __hash__(self) -> int:
        return hash(self.__data)

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def length(self) -> int:
        return len(self.__data)

    @classmethod
    def from_hex(cls, string: str):
        data = hex_decode(string)
        return cls(data=data)

    @classmethod
    def random(cls, length: int):
        data = random_bytes(length=length)
        return cls(data=data)


class IntData(Data):
    """
        Integer data (network ordered)
    """

    def __init__(self, data: bytes, value: int):
        super().__init__(data=data)
        self.__value = value

    def __eq__(self, other) -> bool:
        if isinstance(other, int):
            return self.value == other
        return super().__eq__(other=other)

    @property
    def value(self) -> int:
        return self.__value

    @classmethod
    def from_bytes(cls, data: bytes, byteorder: str='big', signed: bool=False):
        value = bytes_to_int(data=data, byteorder=byteorder, signed=signed)
        return cls(data=data, value=value)

    @classmethod
    def from_int(cls, value: int, length: int, byteorder: str='big', signed: bool=False):
        data = int_to_bytes(value=value, length=length, byteorder=byteorder, signed=signed)
        return cls(data=data, value=value)


class UInt16Data(IntData):
    """
        Unsigned Short Integer (16-bytes)
    """

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = uint16_to_bytes(value)
        super().__init__(data=data, value=value)

    @classmethod
    def from_uint16(cls, value: int, byteorder: str='big', signed: bool=False):
        return cls.from_int(value=value, length=2, byteorder=byteorder, signed=signed)


class UInt32Data(IntData):
    """
        Unsigned Integer (32-bytes)
    """

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = uint32_to_bytes(value)
        super().__init__(data=data, value=value)

    @classmethod
    def from_uint32(cls, value: int, byteorder: str='big', signed: bool=False):
        return cls.from_int(value=value, length=4, byteorder=byteorder, signed=signed)


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
    def parse(cls, data: bytes, length: int=2):
        data_len = len(data)
        if data_len < length:
            return None
        elif data_len > length:
            data = data[:length]
        return cls(data=data)


class Length(IntData):

    @classmethod
    def parse(cls, data: bytes, length: int=2):
        data_len = len(data)
        if data_len < length:
            return None
        elif data_len > length:
            data = data[:length]
        return super().from_bytes(data=data)


class Value(Data):

    @classmethod
    def parse(cls, data: bytes, length: int):
        data_len = len(data)
        if data_len < length:
            return None
        elif data_len > length:
            data = data[:length]
        return cls(data=data)


class TLV:

    def __init__(self, data: bytes, t: Type, v: Value):
        super().__init__()
        self.__data = data
        self.__type = t
        self.__value = v

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def type(self) -> Type:
        return self.__type

    @property
    def value(self) -> Value:
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
        else:
            data = data[_type.length:]
        # get length
        _len = cls.parse_length(data=data, t=_type)
        if _len is not None:
            data = data[_len.length:]
        # get value
        _value = cls.parse_value(data=data, t=_type, length=_len)
        # build data
        data = _type.data
        if _len is not None:
            data += _len.data
        if _value is not None:
            data += _value.data
        return cls(data=data, t=_type, v=_value)

    @classmethod
    def parse_type(cls, data: bytes) -> Optional[Type]:
        return Type.parse(data=data)

    # noinspection PyUnusedLocal
    @classmethod
    def parse_length(cls, data: bytes, t: Type) -> Optional[Length]:
        return Length.parse(data=data)

    # noinspection PyUnusedLocal
    @classmethod
    def parse_value(cls, data: bytes, t: Type, length: Length=None) -> Optional[Value]:
        if length is None or length.value <= 0:
            return None
        else:
            length = length.value
        # check length
        data_len = len(data)
        if data_len < length:
            return None
        if data_len > length:
            data = data[:length]
        return Value.parse(data=data, length=length)
