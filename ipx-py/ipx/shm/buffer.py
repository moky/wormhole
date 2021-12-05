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

from typing import Optional, Union


class CycledBuffer:
    """
        Cycled Buffer
        ~~~~~~~~~~~~~

        Header:
            magic code             - 14 bytes
            offset of read offset  - 1 byte  # the highest bit is for alternate
            offset of write offset - 1 byte  # the highest bit is for alternate
            read offset            - 2/4/8 bytes
            alternate read offset  - 2/4/8 bytes
            write offset           - 2/4/8 bytes
            alternate write offset - 2/4/8 bytes
        Body:
            data zone
    """

    MAGIC_CODE = b'CYCLED BUFFER\0'

    def __init__(self, buffer):
        super().__init__()
        self.__buffer = buffer
        buf_len = len(buffer)
        if buf_len <= 0xFFFF:
            self.__int_len = 2
        elif buffer <= 0xFFFFFFFF:
            self.__int_len = 4
        else:
            self.__int_len = 8
        # check header
        pos = len(self.MAGIC_CODE)  # 14
        self.__pos1 = pos
        self.__pos2 = pos + 1  # 15
        if buffer[:pos] == self.MAGIC_CODE:
            # already initialized
            pos += 2 + (self.__int_len << 2)  # 24/32/48
        else:
            # init with magic code
            buffer[:pos] = self.MAGIC_CODE
            # init pos of read/write pos
            pos1 = pos + 2  # 16
            pos2 = pos1 + (self.__int_len << 1)  # 20/24/32
            buffer[self.__pos1] = pos1
            buffer[self.__pos2] = pos2
            # clear 4 integers for offsets
            pos2 += self.__int_len << 1  # 24/32/48
            buffer[pos1:pos2] = bytearray(pos2 - pos1)
            pos = pos2
        # data zone: [start, end)
        self.__start = pos
        self.__end = buf_len

    @property
    def capacity(self) -> int:
        """ total spaces (leave 1 space not used forever) """
        return self.__end - self.__start - 1

    @property
    def is_empty(self) -> bool:
        p1 = self.read_offset
        p2 = self.write_offset
        return p1 == p2

    @property
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
        offset = self.__buffer[pos_x] & 0x7F  # clear alternate flag
        value = int_from_buffer(buffer=self.__buffer, offset=offset, length=self.__int_len)
        return value + self.__start

    def __update_offset(self, pos_x: int, value: int):
        """ update pointer with alternate spaces """
        pos = self.__buffer[pos_x]
        if pos & 0x80 == 0:
            offset = pos + self.__int_len
            pos = offset | 0x80  # set alternate flag
        else:
            offset = (pos & 0x7F) - self.__int_len
            pos = offset
        # update on alternate spaces
        value -= self.__start
        int_to_buffer(value=value, buffer=self.__buffer, offset=offset, length=self.__int_len)
        # switch after spaces updated
        self.__buffer[pos_x] = pos

    @property
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

    @property
    def spaces(self) -> int:
        """ empty spaces """
        p1 = self.read_offset
        p2 = self.write_offset
        if p1 == p2:
            # empty
            spaces = self.__end - self.__start
        elif p1 > p2:
            spaces = p1 - p2
        else:
            # space separated to two parts
            part1 = self.__end - p2
            part2 = p1 - self.__start
            spaces = part1 + part2
        return spaces - 1  # leave 1 space not used forever

    def read(self, length: int) -> Optional[bytes]:
        """ get one data, measured with size (as leading 4 bytes) """
        available = self.available
        if available < length:
            return None
        buffer = self.__buffer
        start = self.__start
        end = self.__end
        p1 = self.read_offset
        p2 = p1 + length
        if p2 < end:
            data = buffer[p1:p2]
        elif p2 == end:
            # data on the tail
            data = buffer[p1:p2]
            p2 = start
        else:
            # join data as two parts
            p2 = start + p2 - end
            data = buffer[p1:end] + buffer[start:p2]
        # update the pointer after data read
        self.read_offset = p2
        return data

    def write(self, data: Union[bytes, bytearray]) -> bool:
        """ append data with size (as leading 4 bytes) into buffer """
        buffer = self.__buffer
        start = self.__start
        end = self.__end
        p1 = self.write_offset
        p2 = p1 + len(data)
        if p2 < end:
            buffer[p1:p2] = data
        elif p2 == end:
            # data on the tail
            buffer[p1:p2] = data
            p2 = start
        else:
            # separate data to two parts
            m = end - p1
            p2 = start + p2 - end
            buffer[p1:end] = data[:m]
            buffer[start:p2] = data[m:]
        # update the pointer after data wrote
        self.write_offset = p2
        return True


def int_from_buffer(buffer, offset: int = 0, length: int = 4) -> int:
    if 0 < offset or length < len(buffer):
        buffer = buffer[offset:(offset + length)]
    return int.from_bytes(bytes=buffer, byteorder='big', signed=False)


def int_to_buffer(value: int, buffer=None, offset: int = 0, length: int = 4) -> Optional[bytes]:
    data = value.to_bytes(length=length, byteorder='big', signed=False)
    if buffer is None:
        return data
    buffer[offset:(offset + length)] = data
