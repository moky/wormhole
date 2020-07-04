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

from .utils import bytes_to_int
from .utils import random_bytes
from .utils import adjust, adjust_e


class Data:
    """
        Data View
    """

    ZERO = None  # Data(data=b'')

    def __init__(self, data, offset: int=0, length: int=None):
        """
        Create data view

        :param data:   bytes, bytearray or another data view
        :param offset: data view offset
        :param length: data view length
        """
        super().__init__()
        assert data is not None, 'buffer empty'
        if isinstance(data, Data):
            # clone data view
            self._buffer = data._buffer
            self._buf_length = data._buf_length
            self._offset = data._offset
            self._length = data._length
        else:
            # create data view with bytes (or bytearray)
            self._buffer = data
            self._buf_length = len(data)
            self._offset = offset
            if length is None:
                self._length = self._buf_length
            else:
                self._length = length

    def equals(self, buffer: Union[bytes, bytearray], offset: int=0, length: int=None) -> bool:
        if length is None:
            length = len(buffer)
        if self._buffer is buffer:
            # same buffer, checking range
            if self._length == length and self._offset == offset:
                return True
        if self._length != length:
            return False
        pos1 = self._offset + self._length - 1
        pos2 = offset + length - 1
        while pos2 > offset:
            if self._buffer[pos1] != buffer[pos2]:
                return False
            pos1 -= 1
            pos2 -= 1
        return True

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if isinstance(other, Data):
            return self.equals(buffer=other._buffer, offset=other._offset, length=other._length)
        if isinstance(other, bytes) or isinstance(other, bytearray):
            return self.equals(buffer=other)

    def __hash__(self) -> int:
        result = 1
        start = self._offset
        end = start + self._length
        while start < end:
            result = (result << 5) - result + self._buffer[start]
            start += 1
        return result

    @property
    def length(self) -> int:
        return self._length

    @property
    def is_empty(self) -> bool:
        return self._length <= 0

    #
    #   To byte/bytes
    #

    def get_byte(self, index: int) -> int:
        # check position
        if index < 0:
            index += self._length
            if index < 0:
                # too small
                raise IndexError('error index: %d, length: %d' % (index - self._length, self._length))
        elif index >= self._length:
            # too big
            raise IndexError('error index: %d, length: %d' % (index, self._length))
        return self._buffer[index]

    def get_bytes(self, start: int=0, end: int=None) -> bytes:
        if end is None:
            end = self._length
        # adjust positions
        start = self._offset + adjust(position=start, length=self._length)
        end = self._offset + adjust(position=end, length=self._length)
        # check range
        if start == 0 and end == self._buf_length:
            # whole buffer
            if isinstance(self._buffer, bytes):
                return self._buffer
            else:
                return bytes(self._buffer)
        elif start > end:
            raise IndexError('error index: %d, %d' % (start, end))
        elif start == end:
            # empty buffer
            return b''
        # copy sub-array
        if isinstance(self._buffer, bytes):
            return self._buffer[start:end]
        else:
            return bytes(self._buffer)[start:end]

    #
    #   To integer
    #

    def __get_integer_value(self, start: int, size: int) -> int:
        assert size > 0, 'data size error'
        # check position
        start = adjust_e(position=start, length=self._length)
        end = start + size
        if end > self._length:
            raise IndexError('error index: %d, size: %d, length: %d' % (start, size, self._length))
        start += self._offset
        end += self._offset
        return bytes_to_int(data=self._buffer[start:end])

    def get_uint8_value(self, start: int=0) -> int:
        return self.__get_integer_value(start=start, size=1)

    def get_uint16_value(self, start: int=0) -> int:
        return self.__get_integer_value(start=start, size=2)

    def get_uint32_value(self, start: int=0) -> int:
        return self.__get_integer_value(start=start, size=4)

    #
    #   To data view
    #

    def slice(self, start: int=0, end: int=None):  # -> Data:
        if end is None:
            end = self._length
        # adjust positions
        start = adjust(position=start, length=self._length)
        end = adjust(position=end, length=self._length)
        if start == 0 and end == self._length:
            return self
        elif start >= end:
            return Data.ZERO
        offset = self._offset + start
        length = end - start
        return Data(data=self._buffer, offset=offset, length=length)

    def concat(self, other, start: int=0, end: int=None):  # -> Data:
        if isinstance(other, Data):
            # adjust positions
            start = adjust(position=start, length=other._length)
            if end is None:
                end = other._length
            else:
                end = adjust(position=end, length=other._length)
            length = end - start
            if length < 0:
                raise IndexError('error index: %d, %d, length: %d' % (start, end, other._length))
            elif length == 0:
                # other view empty, return this view
                return self
            elif self._length == 0:
                # this view empty, return other view
                return other.slice(start=start, end=end)
            elif self._buffer is other._buffer:
                # same buffer
                if self._offset + self._length == other._offset + start:
                    # join the neighbour views
                    length += self._length
                    return Data(data=self._buffer, offset=self._offset, length=length)
            # right part
            if isinstance(other._buffer, bytes):
                buffer = other._buffer
            else:
                buffer = bytes(other._buffer)
            start += other._offset
            end += other._offset
            if start == 0 and end == other._buf_length:
                buf2 = buffer
            else:
                buf2 = buffer[start:end]
            # left part
            if isinstance(self._buffer, bytes):
                buffer = self._buffer
            else:
                buffer = bytes(self._buffer)
            if self._offset == 0 and self._length == self._buf_length:
                buf1 = buffer
            else:
                start = self._offset
                end = start + self._length
                buf1 = buffer[start:end]
            joined = buf1 + buf2
            return Data(data=joined)
        else:
            # bytes, bytearray
            return self.concat(other=Data(data=other), start=start, end=end)

    @classmethod
    def random(cls, length: int):  # -> Data:
        return cls(data=random_bytes(length=length))


Data.ZERO = Data(data=b'')
