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

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Union


class ByteArray(ABC):

    @property
    def buffer(self) -> Union[bytes, bytearray]:
        """
        Get inner buffer

        :return: bytearray when it's mutable, or bytes for immutable
        """
        raise NotImplemented

    @property
    def offset(self) -> int:
        """
        Get view offset

        :return: 0 ~ (len(buffer) - 1)
        """
        raise NotImplemented

    @property
    def size(self) -> int:
        """
        Get view size

        :return: 0 ~ (len(buffer) - offset)
        """
        raise NotImplemented

    @property
    def hex_string(self) -> str:
        """
        Get Hex encoded string

        :return: hex string
        """
        raise NotImplemented

    @abstractmethod
    def get_byte(self, index: int) -> int:
        """
        Get item value with position

        :param index: position
        :return: item value
        """
        raise NotImplemented

    @abstractmethod
    def get_bytes(self, start: int = 0, end: int = None) -> bytes:
        """
        Get bytes from inner buffer with range [offset, offset + length)

        :param start: begin position relative to offset (include)
        :param end:   end position relative to offset (exclude)
        :return: data bytes
        """
        raise NotImplemented

    @abstractmethod
    def slice(self, start: int, end: int = None):  # -> ByteArray:
        raise NotImplemented

    @abstractmethod
    def concat(self, other):  # -> ByteArray:
        raise NotImplemented

    @abstractmethod
    def find(self, sub, start: int = 0, end: int = None) -> int:
        """
        Search sub data/buffer within range [start, end)

        :param sub:   element value; or sub bytes; or sub array
        :param start: begin position relative to self.offset (include)
        :param end:   end position relative to self.offset (exclude)
        :return: first position where sub occurred; -1 on not found
        """
        raise NotImplemented


class MutableByteArray(ByteArray, ABC):

    @abstractmethod
    def set_byte(self, index: int, value: int):
        """
        Change byte value at this position

        :param index: position
        :param value: byte value
        """
        raise NotImplemented

    @abstractmethod
    def set_char(self, index: int, value: str):
        raise NotImplemented

    @abstractmethod
    def update(self, index: int, source: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None):
        """
        Update values from source data/buffer with range [start, end)

        :param index:  update buffer from this relative position
        :param source: source data/buffer
        :param start:  source start position (include)
        :param end:    source end position (exclude)
        """
        raise NotImplemented

    @abstractmethod
    def append(self, source: Union[bytes, bytearray, ByteArray], start: int = 0, end: int = None):
        """
        Append values from source data/buffer/value with range [start, end)

        :param source: source data/buffer
        :param start:  source start position (include)
        :param end:    source end position (exclude)
        """
        raise NotImplemented

    @abstractmethod
    def insert(self, index: int, source: Union[bytes, bytearray, ByteArray], start: int, end: int = None):
        """
        Append values from source data/buffer/value with range [start, end)

        :param index:  insert buffer from this relative position
        :param source: source data/buffer
        :param start:  source start position (include)
        :param end:    source end position (exclude)
        """
        raise NotImplemented

    @abstractmethod
    def remove(self, index: int) -> int:
        """
        Remove element at this position and return its value

        :param index: position
        :return: element value removed
        """
        raise NotImplemented

    @abstractmethod
    def shift(self) -> int:
        """
        Remove element from the head position and return its value

        :return: element value at the first place
        """
        raise NotImplemented

    @abstractmethod
    def pop(self) -> int:
        """
        Remove element from the tail position and return its value

        :return: element value at the last place
        """
        raise NotImplemented

    @abstractmethod
    def push(self, element: int):
        """
        Append the element to the tail

        :param element: value
        """
        raise NotImplemented


"""
    Integer Data
    ~~~~~~~~~~~~
"""


class Endian(IntEnum):
    UNDEFINED = 0
    BIG_ENDIAN = 1  # Network Byte Order
    LITTLE_ENDIAN = 2  # Host Byte Order


# noinspection PyAbstractClass
class IntegerData(ByteArray, ABC):

    @property
    def endian(self) -> Endian:
        raise NotImplemented

    @property
    def value(self) -> int:
        raise NotImplemented

    @classmethod
    def get_value(cls, source: Union[bytes, bytearray, ByteArray],
                  start: int, size: int, endian: Endian) -> int:
        """
        Get integer value from source data/buffer within range [start, start+size)

        :param source: data or buffer
        :param start:  start position (include)
        :param size:   bytes count
        :param endian: Endian
        :return: int value
        """
        assert start >= 0 and size > 0, 'range error: start=%d, size=%d' % (start, size)
        if isinstance(source, ByteArray):
            start += source.offset
            source = source.buffer
        assert (start + size) <= len(source), 'length error: start=%d, size=%d, len=%d' % (start, size, len(source))
        result = 0
        if endian == Endian.LITTLE_ENDIAN:
            # [12 34 56 78] => 0x78563412
            pos = start + size - 1
            while pos >= start:
                result = (result << 8) | (source[pos] & 0xFF)
                pos -= 1
        elif endian == Endian.BIG_ENDIAN:
            # [12 34 56 78] => 0x12345678
            pos = start
            end = start + size
            while pos < end:
                result = (result << 8) | (source[pos] & 0xFF)
                pos += 1
        return result

    @classmethod
    def set_value(cls, value: int, data: Union[bytes, bytearray, MutableByteArray],
                  start: int, size: int, endian: Endian):
        """
        Set integer value into data/buffer
        """
        if isinstance(data, MutableByteArray):
            data.set_byte(index=(start + size - 1), value=0x00)  # for expanding spaces
            start += data.offset
            data = data.buffer
        if endian == Endian.LITTLE_ENDIAN:
            # 0x12345678 => [78 56 34 12]
            pos = start
            end = start + size
            while pos < end:
                data[pos] = value & 0xFF
                value >>= 8
                pos += 1
        elif endian == Endian.BIG_ENDIAN:
            # 0x12345678 => [12 34 56 78]
            pos = start + size - 1
            while pos >= start:
                data[pos] = value & 0xFF
                value >>= 8
                pos -= 1


#
#   Global Helpers
#
global_instances = {
    'data_helper': None,
    'mutable_helper': None,
    'integer_helper': None,
}


def get_data_helper():
    helper = global_instances['data_helper']
    from .helper import ByteArrayHelper
    assert isinstance(helper, ByteArrayHelper)
    return helper


def set_data_helper(helper):
    global_instances['data_helper'] = helper


def get_mutable_helper():
    helper = global_instances['mutable_helper']
    from .helper import MutableByteArrayHelper
    assert isinstance(helper, MutableByteArrayHelper)
    return helper


def set_mutable_helper(helper):
    global_instances['mutable_helper'] = helper


def get_integer_helper():
    helper = global_instances['integer_helper']
    from .helper import IntegerHelper
    assert isinstance(helper, IntegerHelper)
    return helper


def set_integer_helper(helper):
    global_instances['integer_helper'] = helper
