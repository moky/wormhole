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

from typing import Optional

from .array import ByteArray, IntegerData, Endian
from .integer import UInt16Data, UInt32Data


class Convert:
    """
        Network Byte Order Converter
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    @classmethod
    def int_from_data(cls, data: ByteArray, start: int, size: int):
        return IntegerData.get_value(source=data, start=start, size=size, endian=Endian.BIG_ENDIAN)

    @classmethod
    def int16_from_data(cls, data: ByteArray, start: int = 0) -> int:
        return cls.int_from_data(data=data, start=start, size=2)

    @classmethod
    def int32_from_data(cls, data: ByteArray, start: int = 0) -> int:
        return cls.int_from_data(data=data, start=start, size=4)

    #
    #   UInt16Data
    #

    @classmethod
    def uint16data_from_value(cls, value: int) -> UInt16Data:
        return UInt16Data.from_int(value=value, endian=Endian.BIG_ENDIAN)

    @classmethod
    def uint16data_from_buffer(cls, data: ByteArray, start: int = 0) -> Optional[UInt16Data]:
        if start > 0:
            data = data.slice(start=start)
        return UInt16Data.from_data(data=data, endian=Endian.BIG_ENDIAN)

    #
    #   UInt32Data
    #

    @classmethod
    def uint32data_from_value(cls, value: int) -> UInt32Data:
        return UInt32Data.from_int(value=value, endian=Endian.BIG_ENDIAN)

    @classmethod
    def uint32data_from_buffer(cls, data: ByteArray, start: int = 0) -> Optional[UInt32Data]:
        if start > 0:
            data = data.slice(start=start)
        return UInt32Data.from_data(data=data, endian=Endian.BIG_ENDIAN)
