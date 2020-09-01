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

from typing import Union

from .utils import bytes_to_int, int_to_bytes
from .utils import bytes_to_varint, varint_to_bytes
from .data import Data


class IntegerData(Data):
    """
        Integer data (network ordered)
    """

    def __init__(self, data, value: int=None):
        super().__init__(data=data)
        if value is None:
            if isinstance(data, IntegerData):
                value = data.__value
            else:
                raise ValueError('integer value empty, data: %s' % data)
        self.__value = value

    def __eq__(self, other) -> bool:
        if isinstance(other, IntegerData):
            return self.__value == other.__value
        elif isinstance(other, int):
            return self.__value == other
        else:
            return super().__eq__(other=other)

    def __hash__(self) -> int:
        return hash(self.__value)

    def __str__(self) -> str:
        return str(self.__value)

    def __repr__(self) -> str:
        return str(self.__value)

    @property
    def value(self) -> int:
        return self.__value

    #
    #   Factories
    #

    @classmethod
    def from_int(cls, value: int, length: int):
        data = int_to_bytes(value=value, length=length)
        return cls(data=data, value=value)

    @classmethod
    def from_bytes(cls, data: bytes, start: int=0, end: int=None):
        length = len(data)
        if end is None:
            end = length
        if start != 0 or end != length:
            data = data[start:end]
        value = bytes_to_int(data=data)
        return cls(data=data, value=value)

    @classmethod
    def from_data(cls, data: Data):
        end = data._offset + data._length
        return cls.from_bytes(data=data._buffer, start=data._offset, end=end)


def int_from_buffer(data: Union[bytes, bytearray], start: int, end: int) -> int:
    result = 0
    while start < end:
        result = (result << 8) | (data[start] & 0xFF)
        start += 1
    return result


def parse_data(data: Union[Data, bytes, bytearray], length: int) -> (Union[Data, bytes, bytearray], int):
    if isinstance(data, Data):
        data_len = data._length
        assert data_len >= length, 'data length: %s' % data
        start = data._offset
        end = start + length
        value = int_from_buffer(data=data._buffer, start=start, end=end)
        if data_len > length:
            data = data.slice(end=length)
    else:
        # bytes or bytearray
        data_len = len(data)
        assert data_len >= length, 'data length: %s' % data
        value = int_from_buffer(data=data, start=0, end=length)
        if data_len > length:
            data = data[:length]
    return data, value


class UInt8Data(IntegerData):
    """
        Unsigned Char (8-bytes)
    """

    def __init__(self, data: Union[Data, bytes, bytearray]=None, value: int=None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = int_to_bytes(value=value, length=1)
        elif value is None:
            data, value = parse_data(data=data, length=1)
        super().__init__(data=data, value=value)


class UInt16Data(IntegerData):
    """
        Unsigned Short Integer (16-bytes)
    """

    def __init__(self, data: Union[Data, bytes, bytearray]=None, value: int=None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = int_to_bytes(value=value, length=2)
        elif value is None:
            data, value = parse_data(data=data, length=2)
        super().__init__(data=data, value=value)


class UInt32Data(IntegerData):
    """
        Unsigned Integer (32-bytes)
    """

    def __init__(self, data: Union[Data, bytes, bytearray]=None, value: int=None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = int_to_bytes(value=value, length=4)
        elif value is None:
            data, value = parse_data(data=data, length=4)
        super().__init__(data=data, value=value)


class VarIntData(IntegerData):
    """
        Variable Integer
    """

    def __init__(self, data: Union[Data, bytes, bytearray]=None, value: int=None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = varint_to_bytes(value=value)
        elif value is None:
            if isinstance(data, Data):
                assert data._length > 0, 'data empty: %s' % data
                start = data._offset
                end = start + data._length
                value, length = bytes_to_varint(data=data._buffer, start=start, end=end)
                if length < data._length:
                    data = data.slice(end=length)
            else:
                # bytes or bytearray
                assert len(data) > 0, 'data empty: %s' % data
                value, length = bytes_to_varint(data=data)
                if length < len(data):
                    data = data[:length]
        super().__init__(data=data, value=value)
