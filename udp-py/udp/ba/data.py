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

from .utils import hex_encode, random_bytes
from .utils import array_equal, array_hash
from .array import get_data_helper
from .array import ByteArray, MutableByteArray


class Data(ByteArray):
    """
        Data View
    """
    ZERO = None  # Data(buffer=b'')

    def __init__(self, buffer: Union[bytes, bytearray], offset: int = 0, size: int = None):
        """
        Create data view with range [start, end)

        :param buffer: bytes, bytearray or another data view
        :param offset: data view offset
        :param size:   data view size
        """
        super().__init__()
        self._buffer = buffer
        self._offset = offset
        if size is None:
            self._size = len(buffer) - offset
        else:
            self._size = size

    @property  # Override
    def buffer(self) -> Union[bytes, bytearray]:
        return self._buffer

    @property  # Override
    def offset(self) -> int:
        return self._offset

    @property  # Override
    def size(self) -> int:
        return self._size

    def __eq__(self, other) -> bool:
        if other is None:
            return self._size == 0
        elif other is self:
            return True
        elif isinstance(other, ByteArray):
            return array_equal(left_buffer=self._buffer, left_offset=self._offset, left_size=self._size,
                               right_buffer=other.buffer, right_offset=other.offset, right_size=other.size)
        elif isinstance(other, bytes) or isinstance(other, bytearray):
            return array_equal(left_buffer=self._buffer, left_offset=self._offset, left_size=self._size,
                               right_buffer=other, right_offset=0, right_size=len(other))
        else:
            return False

    def __ne__(self, other) -> bool:
        if other is None:
            return self._size > 0
        elif other is self:
            return False
        elif isinstance(other, ByteArray):
            return not array_equal(left_buffer=self._buffer, left_offset=self._offset, left_size=self._size,
                                   right_buffer=other.buffer, right_offset=other.offset, right_size=other.size)
        elif isinstance(other, bytes) or isinstance(other, bytearray):
            return not array_equal(left_buffer=self._buffer, left_offset=self._offset, left_size=self._size,
                                   right_buffer=other, right_offset=0, right_size=len(other))
        else:
            return True

    def __len__(self) -> int:
        return self._size

    def __hash__(self) -> int:
        return array_hash(buffer=self._buffer, offset=self._offset, size=self._size)

    def __str__(self) -> str:
        data = self.get_bytes()
        # return data.decode('utf-8')
        return str(data)

    def __repr__(self) -> str:
        data = self.get_bytes()
        # return data.decode('utf-8')
        return str(data)

    @property  # Override
    def hex_string(self) -> str:
        data = self.get_bytes()
        return hex_encode(data=data)

    # Override
    def get_byte(self, index: int) -> int:
        index = get_data_helper().adjust_e(index=index, size=self._size)
        if index >= self._size:
            # too big
            raise IndexError('error index: %d, size: %d' % (index, self._size))
        return self._buffer[self._offset + index]

    # Override
    def get_bytes(self, start: int = 0, end: int = None) -> bytes:
        start, end = adjust_positions(size=self._size, start=start, end=end)
        sub = get_slice(data=self, start=start, end=end)
        if isinstance(sub, bytearray):
            return bytes(sub)
        else:
            return sub

    # Override
    def slice(self, start: int, end: int = None) -> ByteArray:
        start, end = adjust_positions(size=self._size, start=start, end=end)
        if start == 0 and end == self._size:
            # whole data
            return self
        elif start < end:
            # sub view
            return Data(buffer=self._buffer, offset=(self._offset+start), size=(end-start))
        else:
            # error
            return self.ZERO

    # Override
    def concat(self, other: Union[bytes, bytearray, ByteArray]) -> ByteArray:
        if other is None:
            # other data is empty, take this data
            return self
        if not isinstance(other, ByteArray):
            other = Data(buffer=other)
        if self._size > 0:
            return get_data_helper().concat(left=self, right=other)
        else:
            # this data is empty, take the other one
            return other

    # Override
    def find(self, sub: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None) -> int:
        if not isinstance(sub, ByteArray):
            sub = Data(buffer=sub)
        start, end = adjust_positions(size=self._size, start=start, end=end)
        return get_data_helper().find(sub=sub, data=self, start=start, end=end)

    def mutable_copy(self) -> MutableByteArray:
        data = get_slice(data=self, start=0, end=self._size)
        from .mutable import MutableData
        return MutableData(buffer=data)

    @classmethod
    def random(cls, size: int) -> ByteArray:
        return cls(buffer=random_bytes(size=size))


# get slice with range [start, end)
def get_slice(data: ByteArray, start: int, end: int) -> Union[bytes, bytearray]:
    if start >= end:
        return b''
    start += data.offset
    end += data.offset
    if start == 0 and end == len(data.buffer):
        return data.buffer
    else:
        return data.buffer[start:end]


def adjust_positions(size: int, start: int, end: Optional[int]) -> (int, int):
    helper = get_data_helper()
    start = helper.adjust(index=start, size=size)
    if end is None:
        end = size
    else:
        end = helper.adjust(index=end, size=size)
    return start, end


# empty data
Data.ZERO = Data(buffer=b'')
