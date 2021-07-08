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

from .utils import adjust, adjust_e, array_copy
from .array import ByteArray, MutableByteArray
from .data import Data


class MutableData(Data, MutableByteArray):

    def __init__(self, data: Union[bytes, bytearray, ByteArray] = None,
                 offset: int = 0, size: int = None, capacity: int = 4):
        if data is None:
            assert capacity > 0, 'invalid capacity: %d' % capacity
            data = bytearray(capacity)  # create empty buffer with capacity
        else:
            data = self.__get_bytearray(data=data)
        super().__init__(data=data, offset=offset, size=size)

    @classmethod
    def __get_bytearray(cls, data: Union[bytes, bytearray, ByteArray]) -> bytearray:
        if isinstance(data, MutableData):
            # get bytearray from mutable buffer
            return data._get_slice(start=0, end=data.size)
        elif not isinstance(data, bytearray):
            if isinstance(data, Data):
                # get bytes/bytearray from inner buffer
                data = data._get_slice(start=0, end=data.size)
            elif isinstance(data, ByteArray):
                # get bytes/bytearray from inner buffer
                data = data.get_bytes()
            # convert bytes to bytearray
            if isinstance(data, bytes):
                data = bytearray(data)
            else:
                assert isinstance(data, bytearray), 'data error: %s' % data
        return data

    def set_byte(self, index: int, value: int):
        index = adjust_e(index=index, size=self._size)
        pos = self._offset + index
        if index < self._size:
            # target position is within the range [0, size)
            self._buffer[pos] = value & 0xFF
        else:
            tail = self._offset + self._size
            buf_len = len(self._buffer)
            if pos < buf_len:
                # there are enough spaces on the right
                for i in range(tail, pos):
                    self._buffer[i] = 0
                self._buffer[pos] = value & 0xFF
            else:
                for i in range(tail, buf_len):
                    self._buffer[i] = 0
                for _ in range(buf_len, pos):
                    self._buffer.append(0)
                self._buffer.append(value & 0xFF)
            # size changed
            self._size = index + 1

    def set_char(self, index: int, value: str):
        assert len(value) == 1, 'char value error: %s' % value
        self.set_byte(index=index, value=ord(value[0]))

    @classmethod
    def __get_sub_array(cls, source: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None) -> bytearray:
        source = cls.__get_bytearray(data=source)
        size = len(source)
        if size > 0:
            start = adjust(index=start, size=size)
            if end is None:
                end = size
            else:
                end = adjust(index=end, size=size)
            if start >= end:
                return bytearray()  # range error
            elif 0 < start or end < size:
                return source[start:end]
        return source

    def update(self, index: int, source: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None):
        # get sub bytearray within range [start, end)
        source = self.__get_sub_array(source=source, start=start, end=end)
        size = len(source)
        if size > 0:
            # check position
            index = adjust_e(index=index, size=self._size)
            start = self._offset + index
            size = len(source)
            min_size = index + size
            if min_size <= self._size:
                # the target range is within the current data view
                array_copy(src=source, src_pos=0, dest=self._buffer, dest_pos=start, length=size)
            else:
                self.__update(index=index, source=source)
                self._size = min_size

    def __update(self, index: int, source: bytearray):
        size = len(source)
        start = self._offset + index
        tail = self._offset + self._size
        buf_len = len(self._buffer)
        if start >= buf_len:
            # the target range is outside of the current buffer
            for i in range(tail, buf_len):
                self._buffer[i] = 0
            for _ in range(buf_len, start):
                self._buffer.append(0)
            for i in range(size):
                self._buffer.append(source[i])
        else:
            # clean the gaps if exists: [tail, start)
            for i in range(tail, start):
                self._buffer[i] = 0
            end = start + size
            if end <= buf_len:
                # there are enough spaces on the right
                array_copy(src=source, src_pos=0, dest=self._buffer, dest_pos=start, length=size)
            else:
                # start < buf_len < end
                left = buf_len - start
                # copy the left part
                array_copy(src=source, src_pos=0, dest=self._buffer, dest_pos=start, length=left)
                # append the right part
                for i in range(left, size):
                    self._buffer.append(source[i])

    def append(self, source: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None):
        # get sub bytearray within range [start, end)
        source = self.__get_sub_array(source=source, start=start, end=end)
        size = len(source)
        if size > 0:
            # update from the edge
            self.__update(index=self._size, source=source)
            self._size += size

    def insert(self, index: int, source: Union[bytes, bytearray, ByteArray], start: int, end: int = None):
        # get sub bytearray within range [start, end)
        source = self.__get_sub_array(source=source, start=start, end=end)
        size = len(source)
        if size > 0:
            # check position
            index = adjust_e(index=index, size=self._size)
            if index < self._size:
                # the target range is within the current data view
                index += self._offset
                for i in range(size):
                    self._buffer.insert(index+i, source[i])
                self._size += size
            elif index == self._size:
                # append to tail
                self.__update(index=self._size, source=source)
                self._size += size
            else:
                raise IndexError('error index: %d, size: %d' % (index, self._size))

    def remove(self, index: int) -> int:
        # check position
        index = adjust_e(index=index, size=self._size)
        if index >= self._size:
            # too big
            raise IndexError('error index: %d, size: %d' % (index, self._size))
        elif index == 0:
            # remove the first element
            return self.shift()
        elif index == (self._size - 1):
            # remove the last element
            return self.pop()
        else:
            index += self._offset
            erased = self._buffer[index]
            self._buffer.pop(index=index)
            self._size -= 1
            return erased

    def shift(self) -> int:
        if self._size < 1:
            raise IndexError('data empty!')
        erased = self._buffer[self._offset]
        self._offset += 1
        self._size -= 1
        return erased

    def pop(self) -> int:
        if self._size < 1:
            raise IndexError('data empty!')
        self._size -= 1
        return self._buffer[self._offset + self._size]

    def push(self, element: int):
        self.set_byte(index=self._size, value=element)
