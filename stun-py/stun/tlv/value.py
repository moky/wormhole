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
from typing import TypeVar, Generic, Union, Optional

from udp.ba import ByteArray, Data
from udp.ba import Endian, UInt8Data, UInt16Data, UInt32Data


from .tag import Tag, T
from .length import Length, L


"""
       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |         Type                  |            Length             |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Value (variable)                ....
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""


class Value(ByteArray):
    """ TLV Value """
    pass


V = TypeVar('V')  # Value


class ValueParser(Generic[T, L, V]):
    """ Value Parser """

    @abstractmethod
    def parse_value(self, data: ByteArray, tag: T, length: L) -> Optional[V]:
        """ Parse Value from data with Tag & Length """
        raise NotImplemented


"""
    Values
    ~~~~~~
"""


class Value8(UInt8Data, Value):
    """ Fixed size Value (8 bits) """

    ZERO = None  # Value8.parse(data=UInt8Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> Value8
        """ parse Value """
        if isinstance(data, Value8):
            return data
        data = UInt8Data.from_data(data=data)
        return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> Value8
        data = UInt8Data.from_int(value=value)
        return cls(data=data, value=data.value)


class Value16(UInt16Data, Tag):
    """ Fixed size Value (16 bits) """

    ZERO = None  # Value16.parse(data=UInt16Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> Value16
        """ parse Value """
        if isinstance(data, Value16):
            return data
        data = UInt16Data.from_data(data=data, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> Value16
        data = UInt16Data.from_int(value=value, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)


class Value32(UInt32Data, Tag):
    """ Fixed size Value (32 bits) """

    ZERO = None  # Value32.parse(data=UInt32Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> Value32
        """ parse Value """
        if isinstance(data, Value32):
            return data
        data = UInt32Data.from_data(data=data, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> Value32
        data = UInt32Data.from_int(value=value, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)


class RawValue(Data, Value):
    """ Base Value """

    ZERO = None  # RawValue.parse(data=Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> RawValue
        """ parse Value """
        if isinstance(data, RawValue):
            return data
        return cls(data=data)

    @classmethod
    def new(cls, data: Union[bytes, bytearray, ByteArray]):  # -> RawValue
        return cls(data=data)


class StringValue(Data, Value):
    """ String Value """

    ZERO = None  # StringValue.parse(data=Data.ZERO)

    def __init__(self, data: Union[bytes, bytearray, ByteArray], string: str):
        super().__init__(data=data)
        self.__string = string

    def __str__(self) -> str:
        return self.__string

    def __repr__(self) -> str:
        return self.__string

    @property
    def string(self) -> str:
        return self.__string

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> StringValue
        """ parse Value """
        if isinstance(data, StringValue):
            return data
        string = data.get_bytes().decode('utf-8')
        return cls(data=data, string=string)

    @classmethod
    def new(cls, string: str):  # -> StringValue
        data = string.encode('utf-8')
        return cls(data=data, string=string)


Value8.ZERO = Value8.parse(data=UInt8Data.ZERO)
Value16.ZERO = Value16.parse(data=UInt16Data.ZERO)
Value32.ZERO = Value32.parse(data=UInt32Data.ZERO)
RawValue.ZERO = RawValue.parse(data=Data.ZERO)
StringValue.ZERO = StringValue.parse(data=Data.ZERO)
