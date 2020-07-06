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
from .data import Data


class MutableData(Data):

    def __init__(self, data=None, offset: int=0, length: int=None, capacity: int=4):
        if data is None:
            assert capacity > 0, 'capacity error'
            offset = 0
            length = 0
            data = bytearray(capacity)
        elif isinstance(data, Data):
            offset = 0
            length = data.length
            data = bytearray(data.get_bytes())
        elif isinstance(data, bytes):
            data = bytearray(data)
        else:
            assert isinstance(data, bytearray), 'data error: %s' % data
        super().__init__(data=data, offset=offset, length=length)

    def __resize(self, size: int=8):
        padding = size - self._buf_length
        if padding > 0:
            self._buffer.extend(bytearray(padding))
        self._buf_length = size

    def __expends(self):
        if self._buf_length > 4:
            self.__resize(self._buf_length << 1)
        else:
            self.__resize(8)

    #
    #  Updating
    #

    def set_byte(self, index: int, value: int) -> bool:
        """
        Change byte value at this position

        :param index: position
        :param value: byte value
        :return: False on error
        """
        if index < 0:
            index += self._length  # count from right hand
            if index < 0:
                return False       # too small
        elif index >= self._length:
            # check buffer size
            size = self._offset + index + 1
            if size > self._buf_length:
                # expend the buffer to new size
                self.__resize(size=size)
            self._length = index + 1
        self._buffer[self._offset + index] = value & 0xFF
        return True

    def copy(self, index: int, source: Union[Data, bytes, bytearray], start: int=0, end: int=None):  # -> MutableData
        """
        Copy values from source buffer with range [start, end)

        :param index:  copy to self buffer from this position
        :param source: source buffer
        :param start:  source start position (include)
        :param end:    source end position (exclude)
        :return: self object
        """
        # adjust positions
        if index < 0:
            index += self._length  # count from right hand
            if index < 0:
                # too small
                raise IndexError('error index: %d, length: %d' % (index - self._length, self._length))
        if isinstance(source, Data):
            source_length = source.length
        else:
            source_length = len(source)
        start = adjust(position=start, length=source_length)
        if end is None:
            end = source_length
        else:
            end = adjust(position=end, length=source_length)
        if start < end:
            if isinstance(source, Data):
                start += source._offset
                end += source._offset
                source = source._buffer
            if source is self._buffer:
                # same buffer, check neighbours
                if self._offset + index == start:
                    # nothing changed
                    return self
            copy_len = end - start
            new_size = self._offset + index + copy_len
            if new_size > self._buf_length:
                # expend the buffer to this size
                self.__resize(size=new_size)
            # copy buffer
            dest_pos = self._offset + index
            array_copy(src=source, src_pos=start, dest=self._buffer, dest_pos=dest_pos, length=copy_len)
            # reset view length
            if index + copy_len > self._length:
                self._length = index + copy_len
        return self

    #
    #   Expanding
    #

    def insert(self, index: int, value: int) -> bool:
        # check position
        if index < 0:
            index += self._length  # count from right hand
            if index < 0:
                return False
        if self._offset > 0:
            # empty spaces exists before the queue
            if index == 0:
                # just insert to the head, no need to move elements
                self._offset -= 1
                self._length += 1
                self._buffer[self._offset] = value & 0xFF
            elif index < self._length:
                # move left part
                pos = self._offset - 1
                array_copy(src=self._buffer, src_pos=self._offset, dest=self._buffer, dest_pos=pos, length=index)
                self._buffer[self._offset + index] = value & 0xFF
                self._offset -= 1
                self._length += 1
            elif self._offset + index < self._buf_length:
                # empty spaces exist after the queue,
                # just insert to the tail, no need to move elements
                self._buffer[self._offset + index] = value & 0xFF
                self._length = index + 1
            else:
                # index out of the range, insert directly
                return self.set_byte(index=index, value=value)
        elif index < self._length:
            # check empty spaces
            if self._length >= self._buf_length:
                self.__expends()
            # move right part
            pos = index + 1
            length = self._length - index
            array_copy(src=self._buffer, src_pos=index, dest=self._buffer, dest_pos=pos, length=length)
            self._buffer[index] = value & 0xFF
            self._length += 1
        else:
            # index out of the range, insert directly
            return self.set_byte(index=index, value=value)
        return True

    def append(self, data, start: int=0, end: int=None):  # -> MutableData
        """
        Append one element to the tail
        Append values from source buffer with range [start, end)

        :param data:  source buffer or element value
        :param start: source start position (include)
        :param end:   source end position (exclude)
        :return: self object
        """
        if isinstance(data, int):
            index = self._offset + self._length
            if index >= self._buf_length:
                # expend the buffer for new element
                self.__expends()
            self._buffer[index] = data
            self._length += 1
            return self
        else:
            # bytes, bytearray or Data
            return self.copy(index=self._length, source=data, start=start, end=end)

    #
    #   Erasing
    #

    def remove(self, index: int) -> int:
        """
        Remove element at this position and return its value

        :param index: position
        :return: element value removed
        :raise IndexError on out of bounds
        """
        # check position
        index = adjust_e(position=index, length=self._length)
        if index >= self._length:
            raise IndexError('error index: %d, length: %d' % (index, self._length))
        elif index == (self._length - 1):
            # remove the last element
            return self.pop()
        elif index == 0:
            # remove the first element
            return self.shift()
        erased = self._buffer[index]
        start = index + 1
        length = self._length - start
        array_copy(src=self._buffer, src_pos=start, dest=self._buffer, dest_pos=index, length=length)
        return erased

    def shift(self) -> int:
        """
        Remove element from the head position and return its value

        :return: element value at the first place
        :raise IndexError on data empty
        """
        if self.is_empty:
            raise IndexError('data empty')
        erased = self._buffer[self._offset]
        self._offset += 1
        self._length -= 1
        return erased

    def pop(self) -> int:
        """
        Remove element from the tail position and return its value

        :return: element value at the last place
        :raise IndexError on data empty
        """
        if self.is_empty:
            raise IndexError('data empty')
        self._length -= 1
        return self._buffer[self._length]
