# -*- coding: utf-8 -*-
#
#   BA: Byte Array
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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

from abc import ABC, abstractmethod
from typing import Optional, Union, Tuple

from .utils import array_concat, array_find
from .utils import array_set, array_update, array_insert, array_remove
from .utils import int_from_buffer, int_to_buffer
from .array import set_data_helper, set_mutable_helper, set_integer_helper
from .array import ByteArray, MutableByteArray, Endian
from .data import Data


class ByteArrayHelper(ABC):

    @abstractmethod
    def adjust(self, index: int, size: int) -> int:
        """ Adjust the index with range [0, size) """
        raise NotImplemented

    @abstractmethod
    def adjust_e(self, index: int, size: int) -> int:
        """ Adjust the index with range [0, size), throws when index too small """
        raise NotImplemented

    @abstractmethod
    def concat(self, left: ByteArray, right: ByteArray) -> ByteArray:
        """ left + right """
        raise NotImplemented

    @abstractmethod
    def find(self, sub: ByteArray, data: ByteArray, start: int, end: int) -> int:
        """ Search sub data """
        raise NotImplemented


class MutableByteArrayHelper(ABC):

    @abstractmethod
    def set(self, value: int, index: int, data: MutableByteArray) -> int:
        """ Set value to data at index, return new size """
        raise NotImplemented

    @abstractmethod
    def update(self, src: ByteArray, index: int, data: MutableByteArray) -> int:
        """ Update src to data at index, return new size """
        raise NotImplemented

    @abstractmethod
    def insert(self, src: ByteArray, index: int, data: MutableByteArray) -> int:
        """ Insert src to data at index, return new size """
        raise NotImplemented

    @abstractmethod
    def remove(self, index: int, data: MutableByteArray) -> Tuple[Optional[int], int, int]:
        """ Remove element at index and return its value, new offset & size """
        raise NotImplemented


class IntegerHelper(ABC):

    @abstractmethod
    def get_value(self, buffer: Union[bytes, bytearray], offset: int, size: int, endian: Endian) -> int:
        """ Get integer value from data with range [offset, offset + size) """
        raise NotImplemented

    @abstractmethod
    def set_value(self, value: int, buffer: Union[bytearray], offset: int, size: int, endian: Endian):
        """ Set integer value into data with range [offset, offset + size) """
        raise NotImplemented


#
#   Implementations
#


class DefaultByteArrayHelper(ByteArrayHelper):
    """ Default ByteArrayHelper """

    # Override
    def adjust(self, index: int, size: int) -> int:
        if index < 0:
            index += size  # count from right hand
            if index < 0:
                return 0  # too small
        elif index > size:
            return size  # too big
        return index

    # Override
    def adjust_e(self, index: int, size: int) -> int:
        if index < 0:
            index += size  # count from right hand
            if index < 0:
                # too small
                raise IndexError('error index: %d, size: %d' % (index - size, size))
        return index

    # Override
    def concat(self, left: ByteArray, right: ByteArray) -> ByteArray:
        buffer, offset, size = array_concat(left_buffer=left.buffer, left_offset=left.offset, left_size=left.size,
                                            right_buffer=right.buffer, right_offset=right.offset, right_size=right.size)
        return Data(buffer=buffer, offset=offset, size=size)

    # Override
    def find(self, sub: ByteArray, data: ByteArray, start: int, end: int) -> int:
        if 0 < start or end < data.size:
            # slice
            data = Data(buffer=data.buffer, offset=(data.offset+start), size=(end-start))
        # searching within the range [start, end)
        pos = array_find(sub_buffer=sub.buffer, sub_offset=sub.offset, sub_size=sub.size,
                         buffer=data.buffer, offset=data.offset, size=data.size)
        if pos == -1:
            return -1
        else:
            return pos + start


class DefaultMutableByteArrayHelper(MutableByteArrayHelper):
    """ Default MutableByteArrayHelper """

    # Override
    def set(self, value: int, index: int, data: MutableByteArray) -> int:
        return array_set(index=index, value=value,
                         buffer=data.buffer, offset=data.offset, size=data.size)

    # Override
    def update(self, src: ByteArray, index: int, data: MutableByteArray) -> int:
        return array_update(index=index, src=src.buffer, src_offset=src.offset, src_size=src.size,
                            buffer=data.buffer, offset=data.offset, size=data.size)

    # Override
    def insert(self, src: ByteArray, index: int, data: MutableByteArray) -> int:
        return array_insert(index=index, src=src.buffer, src_offset=src.offset, src_size=src.size,
                            buffer=data.buffer, offset=data.offset, size=data.size)

    # Override
    def remove(self, index: int, data: MutableByteArray) -> Tuple[Optional[int], int, int]:
        return array_remove(index=index, buffer=data.buffer, offset=data.offset, size=data.size)


class DefaultIntegerHelper(IntegerHelper):
    """ Default IntegerHelper """

    # Override
    def get_value(self, buffer: Union[bytes, bytearray], offset: int, size: int, endian: Endian) -> int:
        return int_from_buffer(buffer=buffer, offset=offset, size=size, endian=endian)

    # Override
    def set_value(self, value: int, buffer: Union[bytearray], offset: int, size: int, endian: Endian):
        int_to_buffer(value=value, buffer=buffer, offset=offset, size=size, endian=endian)


# set default helpers
set_data_helper(helper=DefaultByteArrayHelper())
set_mutable_helper(helper=DefaultMutableByteArrayHelper())
set_integer_helper(helper=DefaultIntegerHelper())
