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

import binascii
import random
from typing import Union

from .array import Endian


def hex_encode(data: bytes) -> str:
    return binascii.b2a_hex(data).decode('utf-8')


def hex_decode(string: str) -> bytes:
    return binascii.a2b_hex(string)


def random_bytes(size: int) -> bytes:
    a = [random.choice('0123456789ABCDEF') for _ in range(size << 1)]
    return hex_decode(''.join(a))


def array_copy(src: Union[bytes, bytearray], src_pos: int, dest: bytearray, dest_pos: int, length: int):
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
        #
        #   now we have:
        #       start1 = src_pos,  end1 = src_pos + length,
        #       start2 = dest_pos, end2 = dest_pos + length,
        #       and length > 0
        #
        #   check for intersections:
        #       1. start1 < end1 <= start2 < end2
        #          src:  ********........
        #          dest: ........########
        #       2. start1 < start2 < end1 < end2   (intersected, needs temporary buffer)
        #          src:  ..********......
        #          dest: ......########..
        #       3. start1 == start2 < end1 == end2 (intersected, but skipped)
        #          src:  ....********....
        #          dest: ....########....
        #       4. start2 < start1 < end2 < end1   (intersected, but doesn't need temporary buffer)
        #          src:  ......********..
        #          dest: ..########......
        #       5. start2 < end2 <= start1 < end1
        #          src:  ........********
        #          dest: ########........
        #
        src_end = src_pos + length
        if src_pos < dest_pos < src_end:
            # copy to a temporary buffer
            src = src[src_pos:src_end]
            src_pos = 0
    for i in range(length):
        dest[dest_pos+i] = src[src_pos+i]
    return True


def array_equal(left_buffer: Union[bytes, bytearray], left_offset: int, left_size: int,
                right_buffer: Union[bytes, bytearray], right_offset: int, right_size: int) -> bool:
    """ Check whether buffers equal with range [offset, offset + size) """
    if left_size != right_size:
        return False
    if left_buffer is right_buffer:
        # same buffer
        if left_offset == right_offset and left_size == right_size:
            # same range
            return True
    pos1 = left_offset + left_size - 1
    pos2 = right_offset + right_size - 1
    while pos2 >= right_offset:
        if left_buffer[pos1] != right_buffer[pos2]:
            # not matched
            return False
        pos1 -= 1
        pos2 -= 1
    # all items matched
    return True


def array_hash(buffer: Union[bytes, bytearray], offset: int, size: int) -> int:
    """ Calculate hash code for buffer with range [offset, offset + size) """
    result = 1
    start = offset
    end = offset + size
    while start < end:
        result = (result << 5) - result + buffer[start]
        start += 1
    return result


def array_concat(left_buffer: Union[bytes, bytearray],
                 left_offset: int, left_size: int,
                 right_buffer: Union[bytes, bytearray],
                 right_offset: int, right_size: int) -> (Union[bytes, bytearray], int, int):
    """ Concat two data with range [start, end) and return (buffer, offset, size) """
    if left_size == 0:
        return right_buffer, right_offset, right_size
    elif right_size == 0:
        return left_buffer, left_offset, left_size
    left_end = left_offset + left_size
    right_end = right_offset + right_size
    if left_buffer is right_buffer:
        # same buffer
        if left_end == right_offset:
            # sticky data
            return left_buffer, left_offset, left_size + right_size
    # slice buffers
    if 0 < left_offset or left_end < len(left_buffer):
        left_buffer = left_buffer[left_offset:left_end]
    if 0 < right_offset or right_end < len(right_buffer):
        right_buffer = right_buffer[right_offset:right_end]
    # check types
    if isinstance(left_buffer, bytearray):
        if not isinstance(right_buffer, bytearray):
            # bytearray + bytes
            right_buffer = bytearray(right_buffer)
    elif isinstance(right_buffer, bytearray):
        # bytes + bytearray
        left_buffer = bytearray(left_buffer)
    return left_buffer + right_buffer, 0, left_size + right_size


def array_find(sub_buffer: Union[bytes, bytearray], sub_offset: int, sub_size: int,
               buffer: Union[bytes, bytearray], offset: int, size: int) -> int:
    """ Searching sub data in buffer with range [offset, offset + size) """
    if sub_size <= 0 or sub_size > size:
        # the sub data is empty or too large
        return -1
    # pre check
    start = offset
    end = offset + size
    found = -1
    if buffer is sub_buffer:
        # same buffer
        if offset == sub_offset:
            # the sub.offset matched the start position,
            # it's surely the first position the sub data appeared.
            return 0
        if offset < sub_offset <= (end - sub_size):
            # if sub.offset is in range (start, end - sub.size],
            # the position (sub.offset - self.offset) is matched,
            # but we cannot confirm this is the first position the sub data appeared,
            # so we still need to do searching in range [start, sub.offset + sub.size - 1).
            found = sub_offset - offset
            end = sub_offset + sub_size - 1
    # TODO: Boyer-Moore Searching
    sub_start = sub_offset
    sub_end = sub_offset + sub_size
    if 0 < sub_start or sub_end < len(sub_buffer):
        sub = sub_buffer[sub_start:sub_end]
    else:
        sub = sub_buffer
    # do searching
    pos = buffer.find(sub, start, end)
    if pos == -1:
        return found
    else:
        return pos - offset


def array_set(index: int, value: int, buffer: bytearray, offset: int, size: int) -> int:
    """ Set value at index, return new size """
    pos = offset + index
    tail = offset + size
    buf_len = len(buffer)
    if buf_len <= pos:
        # the target position is outside of the current buffer
        buffer.extend(bytearray(pos - buf_len + 1))
    # set value
    buffer[pos] = value & 0xFF
    # clean the gaps if exist?
    if tail < pos:
        for i in range(tail, pos):
            buffer[i] = 0
    # return the maximum size
    if index < size:
        return size
    else:
        return index + 1


def array_update(index: int, src: Union[bytes, bytearray], src_offset: int, src_size: int,
                 buffer: bytearray, offset: int, size: int) -> int:
    """ Update src from index, return new size """
    src_end = src_offset + src_size
    if src_offset > 0 or src_end < len(src):
        src = src[src_offset:src_end]
    start = offset + index
    end = start + src_size
    tail = offset + size
    buf_len = len(buffer)
    #
    #   now we have:
    #       start = offset + index
    #       end = offset + index + src_size
    #       tail = offset + size
    #       src_size > 0
    #
    #   check for intersections:
    #       1. buf_len <= start < end
    #          src:                  ****
    #          dest: ########........
    #       2. start < buf_len < end
    #          src:                ****
    #          dest: ########........
    #       3. start < end <= buf_len
    #          src:              ****
    #          dest: ########........
    #
    if buf_len <= start:
        # the target range is outside of the current buffer
        if buf_len < start:
            # append the gaps
            buffer.extend(bytearray(start - buf_len))
        # append source data to tail
        buffer.extend(src)
    elif buf_len < end:
        # the target range is partially outside of the current buffer
        mid = buf_len - start
        for i in range(mid):
            # copy the left part
            buffer[start+i] = src[i]
        # append the right part to tail
        buffer.extend(src[mid:])
    else:
        # the target range is totally inside the current buffer
        for i in range(src_size):
            buffer[start+i] = src[i]
    # clean the gaps if exist?
    if tail < start:
        for i in range(tail, start):
            buffer[i] = 0
    # return the new size
    if tail < end:
        return end - offset
    else:
        return tail - offset


def array_insert(index: int, src: Union[bytes, bytearray], src_offset: int, src_size: int,
                 buffer: bytearray, offset: int, size: int) -> int:
    """ Insert src at index, return new size """
    if index < size:
        start = offset + index
        for i in range(src_size):
            buffer.insert(start+i, src[src_offset+i])
        return size + src_size
    else:
        return array_update(index=index,
                            src=src, src_offset=src_offset, src_size=src_size,
                            buffer=buffer, offset=offset, size=size)


def array_remove(index: int, buffer: bytearray, offset: int, size: int) -> (int, int, int):
    """ Remove element at index, return its value and new offset & size """
    pos = offset + index
    if index == 0:
        # remove the first element
        return buffer[pos], offset + 1, size - 1
    elif index == (size - 1):
        # remove the last element
        return buffer[pos], offset, size - 1
    elif 0 < index < (size - 1):
        return buffer.pop(pos), offset, size - 1
    else:
        raise IndexError('error index: %d, size: %d' % (index, size))


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


def varint_from_buffer(buffer: Union[bytes, bytearray], offset: int, size: int) -> (int, int):
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
