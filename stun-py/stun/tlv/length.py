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

from udp.ba import ByteArray
from udp.ba import Endian, IntegerData, UInt8Data, UInt16Data, UInt32Data, VarIntData


from .tag import Tag, T


"""
       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |         Type                  |            Length             |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Value (variable)                ....
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""


class Length(IntegerData):
    """ TLV Length """
    pass


L = TypeVar('L')  # Length


class LengthParser(Generic[T, L]):
    """ Length Parser """

    @abstractmethod
    def parse_length(self, data: ByteArray, tag: T) -> Optional[L]:
        """ Parse Length from data with Tag """
        raise NotImplemented


"""
    Lengths
    ~~~~~~~
"""


class Length8(UInt8Data, Length):
    """ Fixed size Length (8 bits) """

    ZERO = None  # Length8.parse(data=UInt8Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray], tag: Optional[Tag] = None):  # -> Length8
        """ parse Length """
        if isinstance(data, Length8):
            return data
        data = UInt8Data.from_data(data=data)
        return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> Length8
        data = UInt8Data.from_int(value=value)
        return cls(data=data, value=data.value)


class Length16(UInt16Data, Length):
    """ Fixed size Length (16 bits) """

    ZERO = None  # Length16.parse(data=UInt16Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray], tag: Optional[Tag] = None):  # -> Length16
        """ parse Length """
        if isinstance(data, Length16):
            return data
        data = UInt16Data.from_data(data=data, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> Length16
        data = UInt16Data.from_int(value=value, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)


class Length32(UInt16Data, Length):
    """ Fixed size Length (32 bits) """

    ZERO = None  # Length32.parse(data=UInt32Data.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray], tag: Optional[Tag] = None):  # -> Length32
        """ parse Length """
        if isinstance(data, Length32):
            return data
        data = UInt32Data.from_data(data=data, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> Length32
        data = UInt32Data.from_int(value=value, endian=Endian.BIG_ENDIAN)
        return cls(data=data, value=data.value)


class VarLength(VarIntData, Length):
    """ Variable size Length """

    ZERO = None  # VarLength.parse(data=VarIntData.ZERO)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray], tag: Optional[Tag] = None):  # -> VarLength
        """ parse Length """
        if isinstance(data, VarLength):
            return data
        data = VarIntData.from_data(data=data)
        return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> VarLength
        data = VarIntData.from_int(value=value)
        return cls(data=data, value=data.value)


Length8.ZERO = Length8.parse(data=UInt8Data.ZERO)
Length16.ZERO = Length16.parse(data=UInt16Data.ZERO)
Length32.ZERO = Length32.parse(data=UInt32Data.ZERO)
VarLength.ZERO = VarLength.parse(data=VarIntData.ZERO)
