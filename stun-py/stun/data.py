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
from typing import Optional


def hex_decode(string: str) -> bytes:
    return binascii.a2b_hex(string)


def uint8_to_bytes(value: int) -> bytes:
    return IntData.from_int(value, length=1).data


def uint16_to_bytes(value: int) -> bytes:
    return IntData.from_int(value, length=2).data


def uint32_to_bytes(value: int) -> bytes:
    return IntData.from_int(value, length=4).data


def bytes_to_int(data: bytes) -> int:
    return IntData.from_bytes(data).value


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
        value = int.from_bytes(bytes=data, byteorder=byteorder, signed=signed)
        return cls(data=data, value=value)

    @classmethod
    def from_int(cls, value: int, length: int, byteorder: str='big', signed: bool=False):
        data = value.to_bytes(length=length, byteorder=byteorder, signed=signed)
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
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2:
            return None
        elif data_len > 2:
            data = data[:2]
        return cls(data=data)


class Length(IntData):

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2:
            return None
        elif data_len > 2:
            data = data[:2]
        return super().from_bytes(data=data)


class Value(Data):

    @classmethod
    def parse(cls, data: bytes):
        return cls(data=data)


class TLV:

    def __init__(self, data: bytes, t: Type, v: Value):
        super().__init__(self)
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
        return cls(data, _type, _value)

    @classmethod
    def parse_type(cls, data: bytes) -> Optional[Type]:
        return Type.parse(data=data)

    # noinspection PyUnusedLocal
    @classmethod
    def parse_length(cls, data: bytes, t: Type=None) -> Optional[Length]:
        return Length.parse(data=data)

    # noinspection PyUnusedLocal
    @classmethod
    def parse_value(cls, data: bytes, t: Type=None, length: Length=None) -> Optional[Value]:
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
        return Value.parse(data=data)
