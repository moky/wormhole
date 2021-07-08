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

from typing import Union

from .utils import random_bytes
from .utils import adjust, adjust_e
from .array import ByteArray, MutableByteArray


class Data(ByteArray):
    """
        Data View
    """
    ZERO = None  # Data(data=b'')

    def __init__(self, data: Union[bytes, bytearray, ByteArray], offset: int = 0, size: int = None):
        """
        Create data view with range [start, end)

        :param data:   bytes, bytearray or another data view
        :param offset: data view offset
        :param size:   data view size
        """
        super().__init__()
        if isinstance(data, ByteArray):
            self._buffer = data.buffer
            self._offset = data.offset + offset
            available = data.size - offset
        else:
            # bytes or bytearray
            self._buffer = data
            self._offset = offset
            available = len(data) - offset
        assert available >= 0, 'data buffer error: %d, offset=%d' % (available, offset)
        if size is None or size > available:
            self._size = available
        else:
            self._size = size

    @property
    def buffer(self) -> Union[bytes, bytearray]:
        return self._buffer

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def size(self) -> int:
        return self._size

    def equals(self, buffer: Union[bytes, bytearray], offset: int = 0, size: int = None) -> bool:
        if size is None:
            size = len(buffer) - offset
        if self._size != size:
            return False
        elif self._buffer is buffer and self._offset == offset:
            # same buffer
            return True
        pos1 = self._offset + self._size - 1
        pos2 = offset + size - 1
        while pos2 >= offset:
            if self._buffer[pos1] != buffer[pos2]:
                # not matched
                return False
            pos1 -= 1
            pos2 -= 1
        # all items matched
        return True

    def __eq__(self, other) -> bool:
        if other is None or len(other) == 0:
            return self._size == 0
        elif self is other:
            return True
        elif isinstance(other, ByteArray):
            return self.equals(buffer=other.buffer, offset=other.offset, size=other.size)
        elif isinstance(other, bytes) or isinstance(other, bytearray):
            return self.equals(buffer=other)
        else:
            return False

    def __ne__(self, other) -> bool:
        if other is None or len(other) == 0:
            return self._size > 0
        elif self is other:
            return False
        elif isinstance(other, ByteArray):
            return not self.equals(buffer=other.buffer, offset=other.offset, size=other.size)
        elif isinstance(other, bytes) or isinstance(other, bytearray):
            return not self.equals(buffer=other)
        else:
            return True

    def __len__(self) -> int:
        return self._size

    def __hash__(self) -> int:
        result = 1
        start = self._offset
        end = self._offset + self._size
        while start < end:
            result = (result << 5) - result + self._buffer[start]
            start += 1
        return result

    def get_byte(self, index: int) -> int:
        # check position
        index = adjust_e(index=index, size=self._size)
        if index >= self._size:
            # too big
            raise IndexError('error index: %d, size: %d' % (index, self._size))
        return self._buffer[self._offset + index]

    def get_bytes(self, start: int = 0, end: int = None) -> bytes:
        # adjust positions
        start = adjust(index=start, size=self._size)
        if end is None:
            end = self._size
        else:
            end = adjust(index=end, size=self._size)
        # slice
        sub = self._get_slice(start=start, end=end)
        if isinstance(sub, bytearray):
            return bytes(sub)
        else:
            return sub

    def _get_slice(self, start: int, end: int) -> Union[bytes, bytearray]:
        if start < end:
            start += self._offset
            end += self._offset
            return self._buffer[start:end]
        else:
            # error
            return b''

    def slice(self, start: int, end: int = None) -> ByteArray:
        # adjust positions
        start = adjust(index=start, size=self._size)
        if end is None:
            end = self._size
        else:
            end = adjust(index=end, size=self._size)
        # check range [start, end)
        if start == 0 and end == self._size:
            # whole data
            return self
        elif start < end:
            # sub view
            offset = self._offset + start
            size = end - start
            return Data(data=self._buffer, offset=offset, size=size)
        else:
            # error
            return self.ZERO

    def concat(self, other: Union[bytes, bytearray, ByteArray]) -> ByteArray:
        if other is None or len(other) == 0:
            # other data is empty, take this data
            return self
        elif self._size == 0:
            # this data is empty, take the other one
            if isinstance(other, ByteArray):
                return other
            else:
                # bytes or bytearray
                return Data(data=other)
        # check other type
        if isinstance(other, bytearray):
            data = self._get_slice(start=0, end=self._size)
            if isinstance(data, bytearray):
                # bytearray + bytearray
                return Data(data=(data + other))
            else:
                # bytes + bytearray
                return Data(data=(data + bytes(other)))
        elif isinstance(other, bytes):
            data = self._get_slice(start=0, end=self._size)
            if isinstance(data, bytes):
                # bytes + bytes
                return Data(data=(data + other))
            else:
                # bytearray + bytes
                return Data(data=(bytes(data) + other))
        # ByteArray + ByteArray
        assert isinstance(other, ByteArray), 'other data error: %s' % other
        if self._buffer is other.buffer and (self._offset + self._size) == other.offset:
            # sticky data, create new data on the same buffer
            return Data(data=self._buffer, offset=self._offset, size=(self._size + other.size))
        else:
            # create new data and copy left + right
            join = self.get_bytes() + other.get_bytes()
            return Data(data=join)

    def find(self, sub: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None) -> int:
        # adjust positions
        start = adjust(index=start, size=self._size)
        if end is None:
            end = self._size
        else:
            end = adjust(index=end, size=self._size)
        start += self._offset
        end += self._offset
        if isinstance(sub, ByteArray):
            if self._buffer is sub.buffer:
                # same buffer
                if start == sub.offset and (sub.offset + sub.size) <= end:
                    # match header
                    return 0
                if start < sub.offset < (end - sub.size + 1):
                    # if sub.offset is in range (start, end),
                    # the position (sub.offset - this.offset) is matched,
                    # but we cannot confirm this is the first position it appeared,
                    # so we still need to do searching in range [start, sub.offset).
                    end = sub.offset + sub.size
                sub = sub.get_bytes()
            else:
                sub = sub.get_bytes()
        elif self._buffer is sub:
            # match whole buffer?
            return start == 0 and end == len(sub)
        return self._buffer.find(sub, start, end)

    def mutable_copy(self) -> MutableByteArray:
        data = self._get_slice(start=0, end=self._size)
        if isinstance(data, bytes):
            data = bytearray(data)
        from .mutable import MutableData
        return MutableData(data=data)

    @classmethod
    def random(cls, size: int) -> ByteArray:
        return cls(data=random_bytes(size=size))


Data.ZERO = Data(data=b'')
