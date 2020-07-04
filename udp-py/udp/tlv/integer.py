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
        if isinstance(data, IntegerData):
            self.__value = data.__value
        else:
            # bytes, bytearray or Data?
            assert isinstance(value, int), 'value error: %s' % value
            self.__value = value

    def __eq__(self, other) -> bool:
        if isinstance(other, IntegerData):
            return self.__value == other.__value
        return super().__eq__(other=other)

    def __hash__(self) -> int:
        return hash(self.__value)

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


class UInt8Data(IntegerData):
    """
        Unsigned Char (8-bytes)
    """

    def __init__(self, data: Union[Data, bytes]=None, value: int = None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = int_to_bytes(value=value, length=1)
        elif value is None:
            if isinstance(data, Data):
                assert data._length > 0, 'data empty: %s' % data
                value = data._buffer[data._offset] & 0xFF
            elif isinstance(data, bytes):
                assert len(data) > 0, 'data empty: %s' % data
                value = data[0:1] & 0xFF
            else:
                raise TypeError('unknown data: ' % data)
        super().__init__(data=data, value=value)


class UInt16Data(IntegerData):
    """
        Unsigned Short Integer (16-bytes)
    """

    def __init__(self, data: Union[Data, bytes]=None, value: int = None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = int_to_bytes(value=value, length=2)
        elif value is None:
            if isinstance(data, Data):
                assert data._length >= 2, 'data error: %s' % data
                start = data._offset
                end = start + 2
                value = bytes_to_int(data=data._buffer[start:end])
            elif isinstance(data, bytes):
                assert len(data) >= 2, 'data error: %s' % data
                value = bytes_to_int(data=data[0:2])
            else:
                raise TypeError('unknown data: ' % data)
        super().__init__(data=data, value=value)


class UInt32Data(IntegerData):
    """
        Unsigned Integer (32-bytes)
    """

    def __init__(self, data: Union[Data, bytes]=None, value: int = None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = int_to_bytes(value=value, length=4)
        elif value is None:
            if isinstance(data, Data):
                assert data._length >= 4, 'data error: %s' % data
                start = data._offset
                end = start + 4
                value = bytes_to_int(data=data._buffer[start:end])
            elif isinstance(data, bytes):
                assert len(data) >= 4, 'data error: %s' % data
                value = bytes_to_int(data=data[0:4])
            else:
                raise TypeError('unknown data: ' % data)
        super().__init__(data=data, value=value)


class VarIntData(IntegerData):
    """
        Variable Integer
    """

    def __init__(self, data: Union[Data, bytes]=None, value: int = None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = varint_to_bytes(value=value)
        elif value is None:
            if isinstance(data, Data):
                assert data._length > 0, 'data empty: %s' % data
                start = data._offset
                end = start + 4
                value, length = bytes_to_varint(data=data._buffer, start=start, end=end)
                if length < data._length:
                    data = data.slice(end=length)
            elif isinstance(data, bytes) or isinstance(data, bytearray):
                assert len(data) > 0, 'data empty: %s' % data
                value, length = bytes_to_varint(data=data, start=0, end=4)
                if length < len(data):
                    data = data[0:4]
            else:
                raise TypeError('unknown data: ' % data)
        super().__init__(data=data, value=value)
