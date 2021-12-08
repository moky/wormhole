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

from typing import Union, List

from .memory import Memory, int_from_bytes, int_to_bytes
from .cycle import CycledQueue


class GiantQueue(CycledQueue):
    """
        Giant Data Queue
        ~~~~~~~~~~~~~~~~

        If data is too big (more than the whole buffer can load), it will be split to chunks,
        each chunk contains giant size and current offset (two 4 bytes integers, big-endian),
        and use '\r\n' to separate with the payload.

        The size of first chunk must be capacity - 2 (chunk size takes 2 bytes),
        and not greater than 65535, that will be the maximum size of each chunk too.
        So it means each fragment size will not greater than capacity - 12, or 65525.

        Package body(chunk) format:

             0                   1                   2                   3
             0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            |                          giant size                           |
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            |                         giant offset                          |
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            |      '\r'     |     '\n'      |    payload (giant fragment)
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                payload (giant fragment)                    ~
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
    """

    SEPARATOR = b'\r\n'

    def __init__(self, memory: Memory):
        super().__init__(memory=memory)
        # receiving big data
        self.__incoming_giant_size = 0
        self.__incoming_giant_fragment = None
        # sending big data (split to chunks)
        self.__outgoing_giant_chunks: List[Union[bytes, bytearray]] = []

    def __check_package(self, body: Union[bytes, bytearray]) -> Union[bytes, bytearray, None]:
        """ check received package body without leading 2 bytes """
        body_size = len(body)
        if body_size < 65535 and body_size < (self.capacity - 2):
            # small package
            if self.__incoming_giant_fragment is None:
                # no previous chunks waiting to join,
                # so it must be a normal data package.
                return body
            # it's another chunk for giant
        # body_size will not greater than 65535, and capacity - 2
        assert body_size > 10, 'package size error: %s' % body
        assert body[8:10] == self.SEPARATOR, 'package head error: %s' % body
        giant_size = int_from_bytes(data=body[:4])
        giant_offset = int_from_bytes(data=body[4:8])
        if self.__incoming_giant_fragment is None:
            # first chunk for giant
            assert giant_size > (body_size - 10), 'giant size error: %d, body size: %d' % (giant_size, body_size)
            assert giant_offset == 0, 'first offset error: %d, size: %d' % (giant_offset, giant_size)
            self.__incoming_giant_size = giant_size
            self.__incoming_giant_fragment = body[10:]
        else:
            # another chunk for giant
            cache_size = len(self.__incoming_giant_fragment)
            expected_giant_size = self.__incoming_giant_size
            assert giant_size == expected_giant_size, 'giant size error: %d, %d' % (giant_size, expected_giant_size)
            assert giant_offset == cache_size, 'offset error: %d, %d, size: %d' % (giant_offset, cache_size, giant_size)
            cache_size += body_size - 10
            # check whether completed
            if cache_size < expected_giant_size:
                # not completed yet, cache this fragment
                self.__incoming_giant_fragment += body[10:]
            else:
                # giant completed (the sizes must be equal)
                giant = self.__incoming_giant_fragment + body[10:]
                self.__incoming_giant_fragment = None
                self.__incoming_giant_size = 0
                return giant

    # Override
    def shift(self) -> Union[bytes, bytearray, None]:
        """ shift data """
        while True:
            body = super().shift()
            if body is None:
                # no more packages
                return None
            try:
                # check pack for giant
                data = self.__check_package(body=body)
                if data is not None:
                    # complete data
                    return data
            except AssertionError as error:
                print('[SHM] giant error: %s' % error)
                # discard previous fragment
                self.__incoming_giant_size = 0
                self.__incoming_giant_fragment = None
                # return current package to application
                return body

    def __check_chunks(self) -> bool:
        chunks = self.__outgoing_giant_chunks.copy()
        for body in chunks:
            # send again
            if super().push(data=body):
                # package wrote
                self.__outgoing_giant_chunks.pop(0)
            else:
                # failed
                return False
        # all chunks flushed
        return True

    def __split_giant(self, data: Union[bytes, bytearray]) -> List[Union[bytes, bytearray]]:
        data_size = len(data)
        fra_size = self.capacity - 12  # deduct chunk size (2 bytes), giant size and offset (4 + 4 bytes), and '\r\n'
        if fra_size > 65525:
            fra_size = 65525
        assert fra_size < data_size, 'data size error: %d < %d' % (data_size, fra_size)
        head_size = int_to_bytes(value=data_size, length=4)
        chunks = []
        p1 = 0
        while p1 < data_size:
            p2 = p1 + fra_size
            if p2 > data_size:
                p2 = data_size
            # size + offset + '\r\n' + body
            head_offset = int_to_bytes(value=p1, length=4)
            pack = head_size + head_offset + self.SEPARATOR + data[p1:p2]
            chunks.append(pack)
            # next chunk
            p1 = p2
        return chunks

    # Override
    def push(self, data: Union[bytes, bytearray, None]) -> bool:
        """ append data """
        # 1. check delay chunks for giant
        if not self.__check_chunks():
            # traffic jams
            return False
        elif data is None:
            # do nothing
            return True
        # 2. check data
        data_size = len(data)
        if data_size < 65535 and data_size < (self.capacity - 2):
            # small data, send it directly
            return super().push(data=data)
        # 3. split giant, send as chunks
        return self._append_giant(data=data)

    def _append_giant(self, data: Union[bytes, bytearray]) -> bool:
        self.__outgoing_giant_chunks = self.__split_giant(data=data)
        self.__check_chunks()
        return True
