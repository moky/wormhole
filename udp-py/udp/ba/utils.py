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

import base64
import binascii
import random
from typing import Union

from .array import Endian


def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')


def base64_decode(string: str) -> bytes:
    return base64.b64decode(string)


def hex_encode(data: bytes) -> str:
    return binascii.b2a_hex(data).decode('utf-8')


def hex_decode(string: str) -> bytes:
    return binascii.a2b_hex(string)


def random_bytes(size: int) -> bytes:
    a = [random.choice('0123456789ABCDEF') for _ in range(size << 1)]
    return hex_decode(''.join(a))


def array_copy(src: Union[bytearray, bytes], src_pos: int, dest: bytearray, dest_pos: int, length: int):
    """
    Copies an array from the specified source array, beginning at the
    specified position, to the specified position of the destination array.
    A sub-sequence of array components are copied from the source array
    referenced by src to the destination array referenced by dest.
    The number of components copied is equal to the length argument.
    The components at positions srcPos through srcPos+length-1 in the
    source array are copied into positions destPos through destPos+length-1,
    respectively, of the destination array.

    :param src:      the source array.
    :param src_pos:  starting position in the source array.
    :param dest:     the destination array.
    :param dest_pos: starting position in the destination data.
    :param length:   the number of array elements to be copied.
    :return:
    """
    if src is dest:
        # same buffer
        if src_pos == dest_pos:
            # same position, do nothing
            return False
        # copy via a temporary buffer
        src = src[src_pos:(src_pos+length)]
        src_pos = 0
    for i in range(length):
        dest[dest_pos+i] = src[src_pos+i]


#
#  Converting
#

def int_from_buffer(buffer: Union[bytes, bytearray], offset: int, size: int, endian: Endian) -> int:
    """
    Get integer value from data buffer with range [offset, offset + size)

    :param buffer: data buffer
    :param offset: data view offset
    :param size:   data view size
    :param endian  byte order
    :return: int value
    """
    value = 0
    if endian == Endian.LITTLE_ENDIAN:
        # [12 34 56 78] => 0x78563412
        pos = offset + size - 1
        while pos >= offset:
            value = (value << 8) | (buffer[pos] & 0xFF)
            pos -= 1
    elif endian == Endian.BIG_ENDIAN:
        # [12 34 56 78] => 0x12345678
        pos = offset
        end = offset + size
        while pos < end:
            value = (value << 8) | (buffer[pos] & 0xFF)
            pos += 1
    return value


def int_to_buffer(value: int, buffer: bytearray, offset: int, size: int, endian: Endian):
    """
    Set integer value into data buffer with size

    :param value:  int value
    :param buffer: data buffer
    :param offset: data view offset
    :param size:   data view size
    :param endian  byte order
    """
    if endian == Endian.LITTLE_ENDIAN:
        # 0x12345678 => [78 56 34 12]
        pos = offset
        end = offset + size
        while pos < end:
            buffer[pos] = value & 0xFF
            value >>= 8
            pos += 1
    elif endian == Endian.BIG_ENDIAN:
        # 0x12345678 => [12 34 56 78]
        pos = offset + size - 1
        while pos >= offset:
            buffer[pos] = value & 0xFF
            value >>= 8
            pos -= 1


"""
    VarInt
    ~~~~~~

    0zzzzzzz                   <-> 0zzzzzzz
    00yyyyyy yzzzzzzz          <-> 1zzzzzzz 0yyyyyyy
    000xxxxx xxyyyyyy yzzzzzzz <-> 1zzzzzzz 1yyyyyyy 0xxxxxxx
    ...
"""


def varint_from_buffer(buffer: bytes, offset: int, size: int) -> (int, int):
    """
    Get integer value from variable data buffer with range [offset, offset + size)

    :param buffer: data buffer
    :param offset: data view offset
    :param size:   data view size
    :return: int value, data length
    """
    value = 0
    bits = 0
    pos = offset
    end = offset + size
    ch = 0x80
    while (ch & 0x80) != 0:
        if pos >= end:
            # raise ValueError('out of range: [%d, %d)' % (offset, end))
            return 0, 0
        ch = buffer[pos]
        value |= (ch & 0x7F) << bits
        bits += 7
        pos += 1
    # return (value, length)
    return value, pos - offset


def varint_to_buffer(value: int, buffer: bytearray, offset: int, size: int) -> int:
    """
    Set integer value into variable data buffer with range [offset, offset + size)

    :param value:  int value
    :param buffer: data buffer
    :param offset: data view offset
    :param size:   data view size
    :return: data length
    """
    pos = offset
    end = offset + size
    while value > 0x7F:
        if pos >= end:
            raise OverflowError('out of range: [%d, %d), value=%d' % (offset, end, value))
        buffer[pos] = (value & 0x7F) | 0x80
        value >>= 7
        pos += 1
    if pos >= end:
        raise OverflowError('out of range: [%d, %d), value=%d' % (offset, end, value))
    buffer[pos] = (value & 0x7F)
    return pos - offset + 1


#
#  Positioning
#

def adjust(index: int, size: int):
    """
    Adjust the position within [0, size)

    :param index: range position
    :param size:  range length
    :return: correct position
    """
    if index < 0:
        index += size  # count from right hand
        if index < 0:
            return 0   # too small
    elif index > size:
        return size    # too big
    return index


def adjust_e(index: int, size: int):
    if index < 0:
        index += size  # count from right hand
        if index < 0:
            # too small
            raise IndexError('error index: %d, size: %d' % (index - size, size))
    return index
