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

from typing import Optional


def int_from_buffer(buffer, offset: int = 0, length: int = 4) -> int:
    if 0 < offset or length < len(buffer):
        buffer = buffer[offset:(offset + length)]
    return int.from_bytes(bytes=buffer, byteorder='big', signed=False)


def int_to_buffer(value: int, buffer=None, offset: int = 0, length: int = 4) -> Optional[bytes]:
    data = value.to_bytes(length=length, byteorder='big', signed=False)
    if buffer is None:
        return data
    buffer[offset:(offset + length)] = data


class CycledBuffer:
    """
        Cycled Buffer
        ~~~~~~~~~~~~~

        Header:
            magic code   - 14 bytes
            version      - 1 byte (always be 0)
            int length   - 1 byte (always be 4)
            read offset  - 4 bytes
            write offset - 4 bytes
        Body:
            data item(s) - data size (4 bytes) + data (variable length)
    """

    MAGIC_CODE = b'CYCLED BUFFER\0'

    def __init__(self, buffer):
        super().__init__()
        self.__buffer = buffer
        # check header
        pos = len(self.MAGIC_CODE)  # 14
        if buffer[:pos] == self.MAGIC_CODE:
            # already initialized
            assert buffer[pos] == 0, 'version error: %d' % buffer[pos]
            pos += 1  # 15
            self.__int_len = buffer[pos]  # 4
        else:
            # memset
            buffer[:] = 0
            buffer[:pos] = self.MAGIC_CODE
            pos += 1  # 15
            buffer[pos] = 4
            self.__int_len = 4
        pos += 1  # 16
        self.__read_pos = pos
        pos += self.__int_len  # 20
        self.__write_pos = pos
        pos += self.__int_len  # 24
        # data zone: [start, end)
        self.__start = pos  # 24
        self.__end = len(buffer)

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
        value = int_from_buffer(buffer=self.__buffer, offset=self.__read_pos, length=self.__int_len)
        return value + self.__start

    @read_offset.setter
    def read_offset(self, value: int):
        value -= self.__start
        int_to_buffer(value=value, buffer=self.__buffer, offset=self.__read_pos, length=self.__int_len)

    @property
    def write_offset(self) -> int:
        """ pointer for writing """
        value = int_from_buffer(buffer=self.__buffer, offset=self.__write_pos, length=self.__int_len)
        return value + self.__start

    @write_offset.setter
    def write_offset(self, value: int):
        value -= self.__start
        int_to_buffer(value=value, buffer=self.__buffer, offset=self.__write_pos, length=self.__int_len)

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

    def read(self) -> Optional[bytearray]:
        """ get one data, measured with size (as leading 4 bytes) """
        available = self.available
        if available < 4:
            assert available == 0, 'available error: %d' % available
            return None
        buffer = self.__buffer
        start = self.__start
        end = self.__end
        p1 = self.read_offset
        p2 = p1 + 4
        if p2 < end:
            head = buffer[p1:p2]
        elif p2 == end:
            # data on the tail
            head = buffer[p1:p2]
            p2 = start
        else:
            # join data as two parts
            p2 = start + p2 - end
            head = buffer[p1:end] + buffer[start:p2]
        size = int_from_buffer(buffer=head)
        if available < (size + 4):
            raise BufferError('data size error: %d, %d' % (size, available))
        p1 = p2 + size
        if p1 < end:
            data = buffer[p2:p1]
        elif p1 == end:
            # data on the tail
            data = buffer[p2:p1]
            p1 = start
        else:
            # join data as two parts
            p1 = start + p1 - end
            data = buffer[p2:end] + buffer[start:p1]
        # update the pointer after data read
        self.read_offset = p1
        return data

    def write(self, data: bytearray) -> bool:
        """ set data with size (as leading 4 bytes) into buffer """
        spaces = self.spaces
        size = len(data)
        item_size = 4 + size
        if spaces < item_size:
            # not enough space
            return False
        head = int_to_buffer(value=size)
        item = bytearray(head) + data
        buffer = self.__buffer
        start = self.__start
        end = self.__end
        p1 = self.write_offset
        p2 = p1 + item_size
        if p2 < end:
            buffer[p1:p2] = item
        elif p2 == end:
            # data on the tail
            buffer[p1:p2] = item
            p2 = start
        else:
            # separate data to two parts
            m = end - p1
            p2 = start + p2 - end
            buffer[p1:end] = item[:m]
            buffer[start:p2] = item[m:]
        # update the pointer after data wrote
        self.write_offset = p2
        return True
