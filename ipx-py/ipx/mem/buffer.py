# -*- coding: utf-8 -*-
#
#   SHM: Shared Memory
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

from typing import Union

from .memory import int_from_bytes, int_to_bytes
from .memory import Memory, MemoryBuffer


"""
    Protocol:

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'C'      |      'Y'      |      'C'      |      'L'      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'E'      |      'D'      |      ' '      |      'B'      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'U'      |      'F'      |      'F'      |      'E'      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'R'      |       0       | read ptr pos  | write ptr pos |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                           read offset                         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                 alternate read offset                         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                          write offset                         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                alternate write offset                         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                           read offset (xor)                   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                 alternate read offset (xor)                   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                          write offset (xor)                   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                alternate write offset (xor)                   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                           data zone                            
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                    data zone                            
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                    data zone                           ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
"""


MAGIC_CODE = b'CYCLED BUFFER\0'

HEAD_LEN = 48

INT_LEN = 4
XOR_OFFSET = 16  # 4 integers

RP_POS = 14
WP_POS = 15

READ_OFFSETS = [16, 20]
WRITE_OFFSETS = [24, 28]
FIXED_OFFSETS = [16, 20, 24, 28]


def check(memory: Memory) -> bool:
    """ check whether memory initialized """
    if memory.get_bytes(start=0, end=14) != MAGIC_CODE:
        # magic code not match
        return False
    r_pos = memory.get_byte(index=RP_POS)  # from pos(14)
    if r_pos not in READ_OFFSETS:
        # read ptr pos error
        return False
    w_pos = memory.get_byte(index=WP_POS)  # from pos(15)
    if w_pos not in WRITE_OFFSETS:
        # write ptr pos error
        return False
    # OK
    return True


def clean(memory: Memory):
    """ initialize memory """
    # reset magic code
    memory.update(index=0, source=MAGIC_CODE)
    # reset read/write pointers
    memory.set_byte(index=RP_POS, value=16)
    memory.set_byte(index=WP_POS, value=24)
    # clean read/write offsets
    memory.update(index=16, source=(b'\x00' * 16))
    memory.update(index=32, source=(b'\xFF' * 16))  # xor


def fetch_offsets(memory: Memory, ptr_pos: int) -> (int, int):
    """ fetch offset, and its check value too """
    pos = memory.get_byte(index=ptr_pos) & 0x7F  # clear alternate flag
    assert pos in FIXED_OFFSETS, 'pos of offset error: %d' % pos
    # get pointer
    data = memory.get_bytes(start=pos, end=(pos + INT_LEN))
    value = int_from_bytes(data=data)
    # get xor(offset)
    pos += XOR_OFFSET
    xor = memory.get_bytes(start=pos, end=(pos + INT_LEN))
    return value, int_from_bytes(xor)


def select_offset(memory: Memory, ptr_pos: int, retries: int = 8) -> int:
    """
    Get offset from ptr_pos

    :param memory:
    :param ptr_pos: pos of the value pointer
    :param retries:
    :return: value = offset - start
    """
    while True:
        offset, xor = fetch_offsets(memory=memory, ptr_pos=ptr_pos)
        if (offset ^ xor) == 0xFFFFFFFF:
            return offset  # OK
        if retries <= 0:
            # raise AssertionError('offset error: %d, %s, %s' % (offset, bin(offset), bin(xor)))
            return -1
        retries -= 1  # try again


def update_offset(memory: Memory, ptr_pos: int, value: int):
    """
    Update pointer with alternate spaces

    :param memory:
    :param ptr_pos: pos of the value pointer
    :param value: offset - start
    """
    pos = memory.get_byte(index=ptr_pos)
    if pos & 0x80 == 0:
        offset = pos + INT_LEN  # alter forward
        pos = offset | 0x80     # set alternate flag
    else:
        pos &= 0x7F             # clear alternate flag
        offset = pos - INT_LEN  # alter backward
        pos = offset
    assert offset in FIXED_OFFSETS, 'pos of offset error: %d' % pos
    # update pointer on alternate spaces
    memory.update(index=offset, source=int_to_bytes(value=value, length=INT_LEN))
    # update xor value
    xor = value ^ 0xFFFFFFFF
    memory.update(index=(offset + XOR_OFFSET), source=int_to_bytes(value=xor, length=INT_LEN))
    # switch after spaces updated
    memory.set_byte(index=ptr_pos, value=pos)


class CycledBuffer(MemoryBuffer):
    """
        Cycled Memory Buffer
        ~~~~~~~~~~~~~~~~~~~~

        Header:
            magic code                   - 14 bytes
            offset of read offset        - 1 byte  # the highest bit is for alternate
            offset of write offset       - 1 byte  # the highest bit is for alternate
            read offset                  - 4 bytes
            alternate read offset        - 4 bytes
            write offset                 - 4 bytes
            alternate write offset       - 4 bytes
            check read offset            - 4 bytes (xor)
            check alternate read offset  - 4 bytes (xor)
            check write offset           - 4 bytes (xor)
            check alternate write offset - 4 bytes (xor)
        Body:
            data zone                    - starts from pos(48)

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
    """

    def __init__(self, memory: Memory):
        super().__init__()
        self.__mem = memory
        if not check(memory=memory):
            clean(memory=memory)
        # data zone: [start, end)
        self.__start = HEAD_LEN
        self.__end = memory.size

    @property  # Override
    def memory(self) -> Memory:
        return self.__mem

    @property  # Override
    def capacity(self) -> int:
        """ total spaces (leave 1 space not used forever) """
        return self.__end - self.__start - 1

    @property  # Override
    def available(self) -> int:
        """ data length """
        p1 = self.read_offset
        p2 = self.write_offset
        if p1 == p2:
            # empty
            return 0
        elif p1 < p2:
            return p2 - p1
        else:
            # data separated to two parts
            part1 = self.__end - p1
            part2 = p2 - self.__start
            return part1 + part2

    @property  # Override
    def is_empty(self) -> bool:
        p1 = self.read_offset
        p2 = self.write_offset
        return p1 == p2

    @property  # Override
    def is_full(self) -> bool:
        p1 = self.read_offset
        p2 = self.write_offset + 1
        return p1 == p2 or (p1 == self.__start and p2 == self.__end)

    @property
    def read_offset(self) -> int:
        """ pointer for reading """
        try:
            value = select_offset(memory=self.memory, ptr_pos=RP_POS)
            assert 0 <= value < (self.__end - self.__start), 'offset error: %d' % value
            return value + self.__start
        except AssertionError as error:
            self._check_error(error=error)
            # self.error(msg='failed to read data: %s' % error)
            # import traceback
            # traceback.print_exc()
            raise error

    def __update_read_offset(self, offset: int):
        try:
            value = offset - self.__start
            assert 0 <= value < (self.__end - self.__start), 'offset error: %d' % offset
            update_offset(memory=self.memory, ptr_pos=RP_POS, value=value)
        except AssertionError as error:
            self._check_error(error=error)
            # self.error(msg='failed to read data: %s' % error)
            # import traceback
            # traceback.print_exc()
            raise error

    @property
    def write_offset(self) -> int:
        """ pointer for writing """
        try:
            value = select_offset(memory=self.memory, ptr_pos=WP_POS)
            assert 0 <= value < (self.__end - self.__start), 'offset error: %d' % value
            return value + self.__start
        except AssertionError as error:
            self._check_error(error=error)
            # self.error(msg='failed to read data: %s' % error)
            # import traceback
            # traceback.print_exc()
            raise error

    def __update_write_offset(self, offset: int):
        try:
            value = offset - self.__start
            assert 0 <= value < (self.__end - self.__start), 'offset error: %d' % offset
            update_offset(memory=self.memory, ptr_pos=WP_POS, value=value)
        except AssertionError as error:
            self._check_error(error=error)
            # self.error(msg='failed to read data: %s' % error)
            # import traceback
            # traceback.print_exc()
            raise error

    def _check_error(self, error: AssertionError) -> bool:
        msg = str(error)
        if msg.startswith('pos of offset error:'):
            # header error, destroy it
            clean(memory=self.memory)
            return True
        elif msg.startswith('offset error:'):
            # offset(s) error, reset all of them
            clean(memory=self.memory)
            return True

    # Override
    def peek(self, length: int) -> Union[bytes, bytearray, None]:
        """ read data with length, do not move reading pointer """
        available = self.available
        if available < length:
            return None
        start = self.__start
        end = self.__end
        p1 = self.read_offset
        p2 = p1 + length
        memory = self.memory
        if p2 <= end:
            return memory.get_bytes(start=p1, end=p2)
        else:
            # join data as two parts
            p2 = start + p2 - end
            part1 = memory.get_bytes(start=p1, end=end)
            part2 = memory.get_bytes(start=start, end=p2)
            return part1 + part2

    # Override
    def read(self, length: int) -> Union[bytes, bytearray, None]:
        data = self.peek(length=length)
        if data is not None:
            # update the pointer after data read
            offset = self.read_offset + len(data)
            if offset >= self.__end:
                offset = self.__start + offset - self.__end
            self.__update_read_offset(offset=offset)
        return data

    # Override
    def write(self, data: Union[bytes, bytearray]) -> bool:
        size = len(data)
        if self.spaces < size:
            return False
        start = self.__start
        end = self.__end
        p1 = self.write_offset
        p2 = p1 + size
        memory = self.memory
        if p2 < end:
            memory.update(index=p1, source=data)
        elif p2 == end:
            # data on the tail
            memory.update(index=p1, source=data)
            p2 = start
        else:
            # separate data to two parts
            m = end - p1
            p2 = start + p2 - end
            memory.update(index=p1, source=data[:m])
            memory.update(index=start, source=data[m:])
        # update the pointer after data wrote
        self.__update_write_offset(offset=p2)
        return True
