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

from typing import Union, Optional

from .array import get_data_helper, get_mutable_helper
from .array import ByteArray, MutableByteArray
from .data import adjust_positions
from .data import Data


class MutableData(Data, MutableByteArray):

    def __init__(self, buffer: bytearray = None, offset: int = 0, size: int = None, capacity: int = 4):
        if buffer is None:
            assert capacity > 0, 'invalid capacity: %d' % capacity
            buffer = bytearray(capacity)  # create empty buffer with capacity
            offset = 0
            size = 0
        super().__init__(buffer=buffer, offset=offset, size=size)

    # Override
    def set_byte(self, index: int, value: int):
        index = get_data_helper().adjust_e(index=index, size=self._size)
        size = get_mutable_helper().set(value=value, index=index, data=self)
        if size > self._size:
            self._size = size

    # Override
    def set_char(self, index: int, value: str):
        assert len(value) == 1, 'char value error: %s' % value
        self.set_byte(index=index, value=ord(value[0]))

    # Override
    def update(self, index: int, source: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None):
        index = get_data_helper().adjust_e(index=index, size=self._size)
        source = get_sub_data(data=source, start=start, end=end)
        size = get_mutable_helper().update(src=source, index=index, data=self)
        if size > self._size:
            self._size = size

    # Override
    def append(self, source: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None):
        source = get_sub_data(data=source, start=start, end=end)
        size = get_mutable_helper().insert(src=source, index=self._size, data=self)
        if size > self._size:
            self._size = size

    # Override
    def insert(self, index: int, source: Union[bytes, bytearray, ByteArray], start: int, end: int = None):
        index = get_data_helper().adjust_e(index=index, size=self._size)
        source = get_sub_data(data=source, start=start, end=end)
        size = get_mutable_helper().insert(src=source, index=index, data=self)
        if size > self._size:
            self._size = size

    # Override
    def remove(self, index: int) -> int:
        index = get_data_helper().adjust_e(index=index, size=self._size)
        value, offset, size = get_mutable_helper().remove(index=index, data=self)
        if offset > self._offset:
            self._offset = offset
        if size < self._size:
            self._size = size
        return value

    # Override
    def shift(self) -> int:
        if self._size < 1:
            raise IndexError('data empty!')
        erased = self._buffer[self._offset]
        self._offset += 1
        self._size -= 1
        return erased

    # Override
    def pop(self) -> int:
        if self._size < 1:
            raise IndexError('data empty!')
        self._size -= 1
        return self._buffer[self._offset + self._size]

    # Override
    def push(self, element: int):
        self.set_byte(index=self._size, value=element)


def get_sub_data(data: Union[bytes, bytearray, ByteArray], start: int, end: Optional[int]) -> ByteArray:
    if isinstance(data, ByteArray):
        return data.slice(start=start, end=end)
    else:
        start, end = adjust_positions(size=len(data), start=start, end=end)
        return Data(buffer=data, offset=start, size=(end - start))
