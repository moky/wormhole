# -*- coding: utf-8 -*-
#
#   BA: Byte Array
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

from typing import Union, Optional

from .utils import varint_from_buffer, varint_to_buffer
from .array import get_integer_helper
from .array import ByteArray, IntegerData, Endian
from .data import Data


class IntData(Data, IntegerData):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], value: int, endian: Endian = Endian.UNDEFINED):
        if isinstance(data, ByteArray):
            super().__init__(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            super().__init__(buffer=data)
        self.__value = value
        self.__endian = endian

    def __eq__(self, other) -> bool:
        if isinstance(other, IntegerData):
            return self.__value == other.value
        elif isinstance(other, int):
            return self.__value == other
        else:
            return super().__eq__(other=other)

    def __ne__(self, other) -> bool:
        if isinstance(other, IntegerData):
            return self.__value != other.value
        elif isinstance(other, int):
            return self.__value != other
        else:
            return super().__ne__(other=other)

    def __hash__(self) -> int:
        return hash(self.__value)

    def __str__(self) -> str:
        return str(self.__value)

    def __repr__(self) -> str:
        return str(self.__value)

    @property  # Override
    def endian(self) -> Endian:
        return self.__endian

    @property  # Override
    def value(self) -> int:
        return self.__value


class UInt8Data(IntData):
    """
        Unsigned Char (8-bytes)
    """
    ZERO = None  # UInt8Data.from_int(value=0)

    def __init__(self, data: Union[bytes, bytearray, ByteArray], value: int):
        super().__init__(data=data, value=value, endian=Endian.UNDEFINED)

    @classmethod
    def from_data(cls, data: Union[bytes, bytearray, ByteArray]) -> Optional[IntegerData]:
        if isinstance(data, cls):
            return data
        elif isinstance(data, ByteArray):
            size = data.size
            if size < 1:
                return None
            elif size > 1:
                data = data.slice(start=0, end=1)
            value = data.get_byte(index=0)
        else:
            assert isinstance(data, bytes) or isinstance(data, bytearray), 'uint8 data error: %s' % data
            size = len(data)
            if size < 1:
                return None
            elif size > 1:
                data = data[0:1]
            value = data[0]
        return cls(data=data, value=value)

    @classmethod
    def from_int(cls, value: int):
        data = bytearray(1)
        data[0] = value & 0xFF
        return cls(data=data, value=value)


class UInt16Data(IntData):
    """
        Unsigned Short Integer (16-bytes)
    """
    ZERO = None  # UInt16Data.from_int(value=0, endian=Endian.BIG_ENDIAN)

    @classmethod
    def from_data(cls, data: Union[bytes, bytearray, ByteArray], endian: Endian) -> Optional[IntegerData]:
        if isinstance(data, cls):
            return data
        elif isinstance(data, ByteArray):
            size = data.size
            if size < 2:
                return None
            elif size > 2:
                data = data.slice(start=0, end=2)
            value = get_integer_helper().get_value(buffer=data.buffer, offset=data.offset, size=2, endian=endian)
        else:
            assert isinstance(data, bytes) or isinstance(data, bytearray), 'uint16 data error: %s' % data
            size = len(data)
            if size < 2:
                return None
            elif size > 2:
                data = data[0:2]
            value = get_integer_helper().get_value(buffer=data, offset=0, size=2, endian=endian)
        return cls(data=data, value=value, endian=endian)

    @classmethod
    def from_int(cls, value: int, endian: Endian):
        buffer = bytearray(2)
        get_integer_helper().set_value(value=value, buffer=buffer, offset=0, size=2, endian=endian)
        return cls(data=buffer, value=value, endian=endian)


class UInt32Data(IntData):
    """
        Unsigned Integer (32-bytes)
    """
    ZERO = None  # UInt32Data.from_int(value=0, endian=Endian.BIG_ENDIAN)

    @classmethod
    def from_data(cls, data: Union[bytes, bytearray, ByteArray], endian: Endian) -> Optional[IntegerData]:
        if isinstance(data, cls):
            return data
        elif isinstance(data, ByteArray):
            size = data.size
            if size < 4:
                return None
            elif size > 4:
                data = data.slice(start=0, end=4)
            value = get_integer_helper().get_value(buffer=data.buffer, offset=data.offset, size=4, endian=endian)
        else:
            assert isinstance(data, bytes) or isinstance(data, bytearray), 'uint32 data error: %s' % data
            size = len(data)
            if size < 4:
                return None
            elif size > 4:
                data = data[0:4]
            value = get_integer_helper().get_value(buffer=data, offset=0, size=4, endian=endian)
        return cls(data=data, value=value, endian=endian)

    @classmethod
    def from_int(cls, value: int, endian: Endian):
        buffer = bytearray(4)
        get_integer_helper().set_value(value=value, buffer=buffer, offset=0, size=4, endian=endian)
        return cls(data=buffer, value=value, endian=endian)


class VarIntData(IntData):
    """
        Variable Integer
    """
    ZERO = None  # VarIntData.from_int(value=0)

    def __init__(self, data: Union[bytes, bytearray, ByteArray], value: int):
        super().__init__(data=data, value=value, endian=Endian.UNDEFINED)

    @classmethod
    def from_data(cls, data: Union[bytes, bytearray, ByteArray]) -> Optional[IntegerData]:
        if isinstance(data, cls):
            return data
        elif isinstance(data, ByteArray):
            value, size = varint_from_buffer(buffer=data.buffer, offset=data.offset, size=data.size)
            if size == 0:
                return None
            elif size < data.size:
                data = data.slice(start=0, end=size)
            return cls(data=data, value=value)
        else:
            assert isinstance(data, bytes) or isinstance(data, bytearray), 'varint data error: %s' % data
            value, size = varint_from_buffer(buffer=data, offset=0, size=len(data))
            if size == 0:
                return None
            data = Data(buffer=data, offset=0, size=size)
            return cls(data=data, value=value)

    @classmethod
    def from_int(cls, value: int):
        # maximum 8 bytes: 7 * 9 < 8 * 8 < 7 * 10
        buffer = bytearray(10)
        size = varint_to_buffer(value=value, buffer=buffer, offset=0, size=10)
        data = Data(buffer=buffer, offset=0, size=size)
        return cls(data=data, value=value)


#
#  Zero Values
#

UInt8Data.ZERO = UInt8Data.from_int(value=0)
UInt16Data.ZERO = UInt16Data.from_int(value=0, endian=Endian.BIG_ENDIAN)
UInt32Data.ZERO = UInt32Data.from_int(value=0, endian=Endian.BIG_ENDIAN)
VarIntData.ZERO = VarIntData.from_int(value=0)
