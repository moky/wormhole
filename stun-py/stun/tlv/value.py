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
from udp.ba import UInt8Data, UInt16Data, UInt32Data, Convert


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
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt8Data):
            data = UInt8Data.from_data(data=data)
        if data is not None:
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
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt16Data):
            data = Convert.uint16data_from_data(data=data)
        if data is not None:
            return cls(data=data, value=data.value, endian=data.endian)

    @classmethod
    def new(cls, value: int):  # -> Value16
        data = Convert.uint16data_from_value(value=value)
        return cls(data=data, value=data.value, endian=data.endian)


class Value32(UInt32Data, Tag):
    """ Fixed size Value (32 bits) """

    ZERO = None  # Value32.parse(data=UInt32Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> Value32
        """ parse Value """
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt32Data):
            data = Convert.uint32data_from_data(data=data)
        if data is not None:
            return cls(data=data, value=data.value, endian=data.endian)

    @classmethod
    def new(cls, value: int):  # -> Value32
        data = Convert.uint32data_from_value(value=value)
        return cls(data=data, value=data.value, endian=data.endian)


class RawValue(Data, Value):
    """ Base Value """

    ZERO = None  # RawValue.parse(data=Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> RawValue
        """ parse Value """
        if isinstance(data, cls):
            return data
        elif isinstance(data, ByteArray):
            return cls(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            return cls(buffer=data)


class StringValue(Data, Value):
    """ String Value """

    ZERO = None  # StringValue.parse(data=Data.ZERO)

    def __init__(self, data: Union[bytes, bytearray, ByteArray], string: str):
        if isinstance(data, ByteArray):
            super().__init__(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            super().__init__(buffer=data)
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
        if isinstance(data, cls):
            return data
        if isinstance(data, ByteArray):
            data = data.get_bytes()
        string = data.decode('utf-8')
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
