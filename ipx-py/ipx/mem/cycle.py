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
from .queue import Queue


"""
    Protocol:

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'C'      |      'Y'      |      'C'      |      'M'      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'E'      |      'M'      |       0       |    version    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  index size   |  index limit  |   read pos    |   write pos   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                          (reversed)                           |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  (index zone start)        index 0                            ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        ~                            index 1                            ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        ~                              ...                              ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        ~                            index n          (index zone end)  |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  (data zone start)           ...                              ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        ~                              ...                              ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        ~                              ...             (data zone end)  |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    Parameters:
        magic code   : 6 bytes, always be 'CYC' + 'MEM'
        version      : 2 bytes, always be 0x0001
        index size   : 1 byte, always be 4 (uint32)
        index limit  : 1 byte, always be 255 (excludes an extra space never used)
        read offset  : 1 byte, 0 ~ 255 (index offset for reading)
        write offset : 1 byte, 0 ~ 255 (index offset for writing)
        reversed     : 4 bytes, not used now

        index zone   : 1024 bytes after the header
        index n      : 4 bytes, 0 ~ sizeof(data zone), big-endian
        data zone    : the rest buffer after index zone

        index zone start : always 16
        index zone end   : always 1040 (16 + 4 * 256)
        data zone start  : always 1040
        data zone end    : size of the whole buffer

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
"""


MAGIC_CODE = b'CYC' + b'MEM'
VERSION = 1

HEADER_SIZE = 16  # 6 + 2 + 1 + 1 + 1 + 1 + 4

READ_POS = 10
WRITE_POS = 11

INDEX_SIZE = 4     # uint32
INDEX_LIMIT = 255  # max count of indexes
INDEX_ZONE_START = HEADER_SIZE                       # 16
INDEX_ZONE_SIZE = INDEX_SIZE * (INDEX_LIMIT + 1)     # 1024
INDEX_ZONE_END = INDEX_ZONE_START + INDEX_ZONE_SIZE  # 1040

DATA_ZONE_START = INDEX_ZONE_END                     # 1040


class Config:
    """ Parameters for CycMem """

    def __init__(self, mem_size: int):
        super().__init__()
        self.version = VERSION
        # pointer
        self.read_pos = READ_POS
        self.write_pos = WRITE_POS
        # index
        self.index_size = INDEX_SIZE
        self.index_limit = INDEX_LIMIT
        self.index_zone_start = INDEX_ZONE_START
        self.index_zone_end = INDEX_ZONE_END
        self.index_zone_size = INDEX_ZONE_SIZE
        # data
        self.data_zone_start = DATA_ZONE_START
        self.data_zone_end = mem_size
        self.data_zone_size = mem_size - DATA_ZONE_START

    @classmethod
    def check(cls, memory: Memory):
        """ check whether memory initialized correctly """
        assert memory.size >= 2048, 'memory too small: %d' % memory.size
        if memory.get_bytes(start=0, end=6) != MAGIC_CODE:
            # magic code not match
            return None
        if memory.get_bytes(start=6, end=10) != b'\0\1\4\xff':
            # version or index parameters error
            return None
        # OK
        return Config(mem_size=memory.size)

    @classmethod
    def clean(cls, memory: Memory):
        """ initialize memory """
        # reset magic code
        memory.update(index=0, source=MAGIC_CODE)
        # reset version, index parameters and read/write pointers
        memory.update(index=6, source=b'\0\1\4\xff\0\0')
        # clear first index
        memory.update(index=INDEX_ZONE_START, source=b'\0\0\0\0')
        # OK
        return Config(mem_size=memory.size)


def get_idx(memory: Memory, offset: int) -> int:
    """ get index value from index zone with read/write index offset """
    pos = INDEX_ZONE_START + offset * INDEX_SIZE
    buf = memory.get_bytes(start=pos, end=(pos + INDEX_SIZE))
    return int_from_bytes(data=buf)


def get_pos(memory: Memory, offset: int) -> int:
    """ get data position with read/write index offset """
    idx = get_idx(memory=memory, offset=offset)
    pos = idx + DATA_ZONE_START
    if pos < memory.size:
        return pos
    assert pos == memory.size, 'index error: %d + %d, %d' % (DATA_ZONE_START, idx, memory.size)
    return pos - memory.size + DATA_ZONE_START


def get_read_range(memory: Memory) -> (int, int):
    """ get range [start, end) for reading """
    r = memory.get_byte(index=READ_POS)
    w = memory.get_byte(index=WRITE_POS)
    if r == w:
        # index zone empty
        return -1, -1
    # get next index after reading point
    n = r + 1 if r < INDEX_LIMIT else 0
    start = get_pos(memory=memory, offset=r)
    end = get_pos(memory=memory, offset=n)
    if start == end:
        # should not happen
        return -1, -1
    # positions for current index & next index
    return start, end


def get_write_range(memory: Memory) -> (int, int):
    """ get range [start, end) for writing """
    r = memory.get_byte(index=READ_POS)
    w = memory.get_byte(index=WRITE_POS)
    if (w + 1) == r or (r == 0 and w == INDEX_LIMIT):
        # index zone full
        return -1, -1
    rp = get_pos(memory=memory, offset=r)
    if r == w:
        # index zone empty, means data zone empty too
        wp = rp
    else:
        wp = get_pos(memory=memory, offset=w)
        if (wp + 1) == rp or (rp == DATA_ZONE_START and (wp + 1) == memory.size):
            # data zone full
            return -1, -1
    # the reading pointer is pointing to where stored the first data,
    # in order to make a boundary for the writing & reading pointer,
    # we left an empty space before the reading pointer.
    end = rp - 1
    if end < DATA_ZONE_START:
        end += memory.size - DATA_ZONE_START
    # return empty range [wp, end) can be wrote
    return wp, end


def get_positions(memory: Memory) -> (int, int):
    """ get positions for reading, writing """
    r = memory.get_byte(index=READ_POS)
    w = memory.get_byte(index=WRITE_POS)
    rp = get_pos(memory=memory, offset=r)
    if r == w:
        # index zone empty
        return rp, rp
    wp = get_pos(memory=memory, offset=w)
    return rp, wp


def read_data(memory: Memory, start: int, end: int) -> bytes:
    """ read data from range [start, end) """
    if start < end:
        # data stored continuously
        return memory.get_bytes(start=start, end=end)
    elif end == DATA_ZONE_START:
        # data stored to the tail of memory
        return memory.get_bytes(start=start)
    else:
        # data separated to two parts
        left = memory.get_bytes(start=start)
        right = memory.get_bytes(start=DATA_ZONE_START, end=end)
        return left + right


def move_read_pointer(memory: Memory):
    """ move reading pointer forward """
    r = memory.get_byte(index=READ_POS)
    if r < INDEX_LIMIT:
        memory.set_byte(index=READ_POS, value=(r + 1))
    else:
        memory.set_byte(index=READ_POS, value=0)


def write_data(memory: Memory, start: int, end: int, data: Union[bytes, bytearray]) -> int:
    """ write data into memory from start position and return the tail position """
    tail = end - memory.size
    if tail < 0:
        # store data continuously
        memory.update(index=start, source=data)
        return end
    elif tail == 0:
        # store data to the tail
        memory.update(index=start, source=data)
        return DATA_ZONE_START
    else:
        # separate data to two parts
        m = len(data) - tail
        memory.update(index=start, source=data[:m])
        memory.update(index=DATA_ZONE_START, source=data[m:])
        return DATA_ZONE_START + tail


def add_write_position(memory: Memory, pos: int):
    """ add end position just wrote """
    # convert position to data zone offset
    idx = int_to_bytes(value=(pos - DATA_ZONE_START), length=INDEX_SIZE)
    # add new index
    w = memory.get_byte(index=WRITE_POS)
    w = w + 1 if w < INDEX_LIMIT else 0
    memory.update(index=(INDEX_ZONE_START + w * INDEX_SIZE), source=idx)
    # move writing pointer forward
    memory.set_byte(index=WRITE_POS, value=w)


class CycledBuffer(MemoryBuffer):
    """
        Cycled Memory Buffer
        ~~~~~~~~~~~~~~~~~~~~

        Head (16 bytes):
            magic code     - 6 bytes
            version        - 2 bytes (0x0001)
            index size     - 1 byte (0x04)
            index limit    - 1 byte (0xFF)
            read offset    - 1 byte
            write offset   - 1 byte
            reserved       - 4 bytes
        Index Zone (1024 bytes):
            index n        - 4 bytes * 256
        Body:
            data zone      - starts from pos (1040)

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
    """

    def __init__(self, memory: Memory):
        super().__init__()
        self.__mem = memory
        # check memory header
        conf = Config.check(memory=memory)
        if conf is None:
            conf = Config.clean(memory=memory)
        self.__conf = conf

    @property
    def config(self) -> Config:
        return self.__conf

    @property  # Override
    def memory(self) -> Memory:
        return self.__mem

    @property  # Override
    def capacity(self) -> int:
        """ total spaces (leave 1 space not used forever) """
        conf = self.config
        return conf.data_zone_size - 1

    @property  # Override
    def available(self) -> int:
        """ data length """
        memory = self.memory
        rp, wp = get_positions(memory=memory)
        if rp == wp:
            # data zone empty
            return 0
        elif rp < wp:
            # data stored continuously
            return wp - rp
        else:
            # data separated to two parts
            conf = self.config
            return conf.data_zone_end - rp + wp - conf.data_zone_start

    @property  # Override
    def is_empty(self) -> bool:
        memory = self.memory
        rp, wp = get_positions(memory=memory)
        return rp == wp

    @property  # Override
    def is_full(self) -> bool:
        memory = self.memory
        start, end = get_write_range(memory=memory)
        # if start < 0 or end < 0:
        #     return True
        return start == end

    # Override
    def read(self) -> Union[bytes, bytearray, None]:
        memory = self.memory
        # 1. get next range [start, end) for reading
        start, end = get_read_range(memory=memory)
        if start == end:
            # both -1, data zone empty
            return None
        # 2. get data from range [start, end)
        data = read_data(memory=memory, start=start, end=end)
        # 3. move reading pointer forward
        move_read_pointer(memory=memory)
        # OK
        return data

    # Override
    def write(self, data: Union[bytes, bytearray]) -> bool:
        memory = self.memory
        # 1. get range [start, end) for writing
        start, end = get_write_range(memory=memory)
        if start == end:
            # both -1, memory is full
            return False
        # 2. check empty spaces for storing data
        if start < end:
            spaces = end - start
        else:
            conf = self.config
            spaces = conf.data_zone_end - start + end - conf.data_zone_start
        data_size = len(data)
        if spaces < data_size:
            # not enough spaces
            return False
        # 3. write data into data zone with range [start, end),
        #    and append tail position of the data into index zone
        pos = write_data(memory=memory, start=start, end=(start + data_size), data=data)
        add_write_position(memory=memory, pos=pos)
        return True


class CycledQueue(CycledBuffer, Queue):

    # Override
    def shift(self) -> Union[bytes, bytearray, None]:
        return self.read()

    # Override
    def push(self, data: Union[bytes, bytearray, None]) -> bool:
        if data is None:
            # do nothing
            return True
        return self.write(data=data)
