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

import base64
import binascii
import random
from typing import Union


def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')


def base64_decode(string: str) -> bytes:
    return base64.b64decode(string)


def hex_encode(data: bytes) -> str:
    return binascii.b2a_hex(data).decode('utf-8')


def hex_decode(string: str) -> bytes:
    return binascii.a2b_hex(string)


def random_bytes(length: int) -> bytes:
    r = range(length << 1)
    # noinspection PyUnusedLocal
    a = ''.join([random.choice('0123456789ABCDEF') for i in r])
    return hex_decode(a)


def bytes_to_int(data: bytes, byteorder: str='big', signed: bool=False) -> int:
    return int.from_bytes(bytes=data, byteorder=byteorder, signed=signed)


def int_to_bytes(value: int, length: int, byteorder: str='big', signed: bool=False) -> bytes:
    return value.to_bytes(length=length, byteorder=byteorder, signed=signed)


"""
    VarInt
    ~~~~~~

    00xxxxxx xxxxxxxx <-> 1xxxxxxx 0xxxxxxx
"""


def bytes_to_varint(data: bytes, start: int=0, end: int=None) -> (int, int):
    if end is None:
        end = len(data)
    value = 0
    offset = 0
    index = start
    ch = 0x80
    while (ch & 0x80) != 0 and index < end:
        ch = data[index]
        value |= (ch & 0x7F) << offset
        offset += 7
        index += 1
    return value, index - start


def varint_to_bytes(value: int) -> bytes:
    array = bytearray()
    while value > 0x7F:
        array.append((value & 0x7F) | 0x80)
        value >>= 7
    array.append(value & 0x7F)
    return bytes(array)


def adjust(position: int, length: int):
    """
    Adjust the position within [0, length)

    :param position: index/location
    :param length:   range
    :return: correct position
    """
    if position < 0:
        position += length  # count from right hand
        if position < 0:
            return 0        # too small
    elif position > length:
        return length       # too big
    return position


def adjust_e(position: int, length: int):
    """
    Adjust the position within [0, length)

    :param position: index/location
    :param length:   range
    :return: correct position
    """
    if position < 0:
        position += length  # count from right hand
        if position < 0:
            # too small
            raise IndexError('error index: %d, length: %d' % (position - length, length))
    elif position > length:
        # too big
        raise IndexError('error index: %d, length: %d' % (position, length))
    return position


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
    for index in range(length):
        dest[dest_pos + index] = src[src_pos + index]
