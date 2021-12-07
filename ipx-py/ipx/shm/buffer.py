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

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Union


M = TypeVar('M')  # Shared Memory


class CycledBuffer(Generic[M], ABC):
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
    """

    MAGIC_CODE = b'CYCLED MEMORY\0'

    def __init__(self, shm: M):
        super().__init__()
        self.__shm = shm
        bounds = self.size
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
        if self._slice(start=0, end=pos) == self.MAGIC_CODE:
            # already initialized
            pos += 2 + (self.__int_len << 2)  # 24/32/48
        else:
            # init with magic code
            self._update(start=0, end=pos, data=self.MAGIC_CODE)
            # init pos of read/write pos
            pos1 = pos + 2  # 16
            pos2 = pos1 + (self.__int_len << 1)  # 20/24/32
            self._set(pos=self.__pos1, value=pos1)
            self._set(pos=self.__pos2, value=pos2)
            # clear 4 integers for offsets
            pos2 += self.__int_len << 1  # 24/32/48
            self._update(start=pos1, end=pos2, data=bytearray(pos2 - pos1))
            pos = pos2
        # data zone: [start, end)
        self.__start = pos
        self.__end = bounds

    @property
    def shm(self) -> M:
        return self.__shm

    @property
    def size(self) -> int:
        """ Gets buffer length """
        raise NotImplemented

    @abstractmethod
    def _set(self, pos: int, value: int):
        """ Sets value with index """
        raise NotImplemented

    @abstractmethod
    def _get(self, pos: int) -> int:
        """ Gets value from index """
        raise NotImplemented

    @abstractmethod
    def _update(self, start: int, end: int, data: Union[bytes, bytearray]):
        """ Updates slice [start, end) """
        assert start + len(data) == end, 'range error: %d + %d != %d' % (start, len(data), end)
        raise NotImplemented

    @abstractmethod
    def _slice(self, start: int, end: int) -> Union[bytes, bytearray]:
        """ Gets slice [start, end) """
        raise NotImplemented

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
        offset = self._get(pos=pos_x) & 0x7F  # clear alternate flag
        assert 16 <= offset <= (self.__start - self.__int_len), 'pos of offset error: %d' % offset
        data = self._slice(start=offset, end=(offset + self.__int_len))
        value = int_from_buffer(buffer=data)
        assert 0 <= value < (self.__end - self.__start), 'offset error: %d' % value
        return value + self.__start

    def __update_offset(self, pos_x: int, value: int):
        """ update pointer with alternate spaces """
        pos = self._get(pos=pos_x)
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
        data = int_to_buffer(value=value, length=self.__int_len)
        self._update(start=offset, end=(offset + self.__int_len), data=data)
        # switch after spaces updated
        self._set(pos=pos_x, value=pos)

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
        self._update(start=0, end=6, data=b'BROKEN')

    def _clear_data_zone(self):
        p1 = len(self.MAGIC_CODE) + 2
        p2 = self.__start
        size = self.__int_len << 2
        assert size == (p2 - p1), 'header error: %s' % self
        self._update(start=p1, end=p2, data=bytes(size))

    def _try_read(self, length: int) -> (Union[bytes, bytearray, None], int):
        """ read data with length, do not move reading pointer """
        available = self.available
        if available < length:
            return None, -1
        start = self.__start
        end = self.__end
        p1 = self.read_offset
        p2 = p1 + length
        if p2 < end:
            data = self._slice(start=p1, end=p2)
        elif p2 == end:
            # data on the tail
            data = self._slice(start=p1, end=p2)
            p2 = start
        else:
            # join data as two parts
            p2 = start + p2 - end
            part1 = self._slice(start=p1, end=end)
            part2 = self._slice(start=start, end=p2)
            data = part1 + part2
        return data, p2

    def read(self, length: int) -> Union[bytes, bytearray, None]:
        """ get one data, measured with size (as leading 4 bytes) """
        data, offset = self._try_read(length=length)
        if data is not None:
            # update the pointer after data read
            self.read_offset = offset
        return data

    def write(self, data: Union[bytes, bytearray]) -> bool:
        """ append data with size (as leading 4 bytes) into buffer """
        size = len(data)
        if self.spaces < size:
            return False
        start = self.__start
        end = self.__end
        p1 = self.write_offset
        p2 = p1 + size
        if p2 < end:
            self._update(start=p1, end=p2, data=data)
        elif p2 == end:
            # data on the tail
            self._update(start=p1, end=p2, data=data)
            p2 = start
        else:
            # separate data to two parts
            m = end - p1
            p2 = start + p2 - end
            self._update(start=p1, end=end, data=data[:m])
            self._update(start=start, end=p2, data=data[m:])
        # update the pointer after data wrote
        self.write_offset = p2
        return True


def int_from_buffer(buffer: Union[bytes, bytearray]) -> int:
    return int.from_bytes(bytes=buffer, byteorder='big', signed=False)


def int_to_buffer(value: int, length: int = 4) -> Optional[bytes]:
    return value.to_bytes(length=length, byteorder='big', signed=False)
