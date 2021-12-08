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
from .memory import Memory, MemoryPool

"""
    Protocol:

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'C'      |      'Y'      |      'C'      |      'L'      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'E'      |      'D'      |      ' '      |      'M'      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'E'      |      'M'      |      'O'      |      'R'      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'Y'      |       0       | read ptr pos  | write ptr pos |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |          read offset          |     alternate read offset     |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |          write offset         |     alternate write offset    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                           data zone                            
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                    data zone                           ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
"""


class CycledBuffer(MemoryPool):
    """
        Cycled Memory Buffer
        ~~~~~~~~~~~~~~~~~~~~

        Header:
            magic code             - 14 bytes
            offset of read offset  - 1 byte  # the highest bit is for alternate
            offset of write offset - 1 byte  # the highest bit is for alternate
            read offset            - 2/4/8 bytes
            alternate read offset  - 2/4/8 bytes
            write offset           - 2/4/8 bytes
            alternate write offset - 2/4/8 bytes
        Body:
            data zone              - starts from 24/32/48

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
    """

    MAGIC_CODE = b'CYCLED BUFFER\0'

    def __init__(self, memory: Memory):
        super().__init__()
        self.__mem = memory
        bounds = memory.size
        if bounds <= 0x10018:
            # len(header) == 24 bytes
            self.__int_len = 2
        elif bounds <= 0x100000020:
            # len(header) == 32 bytes
            self.__int_len = 4
        else:
            # len(header) == 48 bytes
            self.__int_len = 8
        # check header
        pos = len(self.MAGIC_CODE)  # 14
        self.__pos1 = pos
        self.__pos2 = pos + 1  # 15
        if memory.get_bytes(start=0, end=pos) == self.MAGIC_CODE:
            # already initialized
            pos += 2 + (self.__int_len << 2)  # 24/32/48
        else:
            # init with magic code
            memory.update(index=0, source=self.MAGIC_CODE)
            # init pos of read/write pos
            pos1 = pos + 2  # 16
            pos2 = pos1 + (self.__int_len << 1)  # 20/24/32
            memory.set_byte(index=self.__pos1, value=pos1)
            memory.set_byte(index=self.__pos2, value=pos2)
            # clear 4 integers for offsets
            pos2 += self.__int_len << 1  # 24/32/48
            memory.update(index=pos1, source=bytes(pos2 - pos1))
            pos = pos2
        # data zone: [start, end)
        self.__start = pos
        self.__end = bounds

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
        return self.__fetch_offset(self.__pos1)

    @read_offset.setter
    def read_offset(self, value: int):
        self.__update_offset(self.__pos1, value=value)

    @property
    def write_offset(self) -> int:
        """ pointer for writing """
        return self.__fetch_offset(self.__pos2)

    @write_offset.setter
    def write_offset(self, value: int):
        self.__update_offset(self.__pos2, value=value)

    def __fetch_offset(self, pos_x: int) -> int:
        memory = self.memory
        offset = memory.get_byte(index=pos_x) & 0x7F  # clear alternate flag
        assert 16 <= offset <= (self.__start - self.__int_len), 'pos of offset error: %d' % offset
        data = memory.get_bytes(start=offset, end=(offset + self.__int_len))
        value = int_from_bytes(data=data)
        assert 0 <= value < (self.__end - self.__start), 'offset error: %d' % value
        return value + self.__start

    def __update_offset(self, pos_x: int, value: int):
        """ update pointer with alternate spaces """
        memory = self.memory
        pos = memory.get_byte(index=pos_x)
        if pos & 0x80 == 0:
            offset = pos + self.__int_len
            pos = offset | 0x80  # set alternate flag
        else:
            offset = (pos & 0x7F) - self.__int_len
            pos = offset
        assert 16 <= offset <= (self.__start - self.__int_len), 'pos of offset error: %d' % pos
        # update on alternate spaces
        value -= self.__start
        assert 0 <= value < (self.__end - self.__start), 'offset error: %d' % value
        data = int_to_bytes(value=value, length=self.__int_len)
        memory.update(index=offset, source=data)
        # switch after spaces updated
        memory.set_byte(index=pos_x, value=pos)

    def _check_error(self, error: AssertionError) -> bool:
        msg = str(error)
        if msg.startswith('pos of offset error:'):
            # header error, destroy it
            self._destroy_memory()
            return True
        elif msg.startswith('offset error:'):
            # offset(s) error, reset all of them
            self._clear_data_zone()
            return True

    def _destroy_memory(self):
        self.memory.update(index=0, source=b'BROKEN')

    def _clear_data_zone(self):
        pos = len(self.MAGIC_CODE) + 2
        size = self.__int_len << 2  # 4 integers
        assert size == (self.__start - pos), 'header error: %s' % self
        self.memory.update(index=pos, source=bytes(size))

    def _try_read(self, length: int) -> Union[bytes, bytearray, None]:
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
    def peek(self, length: int) -> Union[bytes, bytearray, None]:
        try:
            return self._try_read(length=length)
        except AssertionError as error:
            self._check_error(error=error)
            # self.error(msg='failed to read data: %s' % error)
            # import traceback
            # traceback.print_exc()
            raise error

    # Override
    def read(self, length: int) -> Union[bytes, bytearray, None]:
        data = self.peek(length=length)
        if data is not None:
            # update the pointer after data read
            offset = self.read_offset + len(data)
            if offset >= self.__end:
                offset = self.__start + offset - self.__end
            self.read_offset = offset
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
        self.write_offset = p2
        return True
