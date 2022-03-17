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


"""
    Package body(chunk) format:

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                          giant size                           |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                         giant offset                          |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                 check for giant size & offset                 |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                   payload (giant fragment)
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                            payload (giant fragment)                    ~
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
"""


def parse_giant_head(data: bytes) -> (int, int):
    """ get giant size & offset """
    size = int_from_bytes(data=data[0:4])
    offset = int_from_bytes(data=data[4:8])
    check = int_from_bytes(data=data[8:12])
    assert size ^ offset ^ check == 0xFFFFFFFF, 'xor check error: size=%d, offset=%d, %s, %s, %s'\
                                                % (size, offset, bin(size), bin(offset), bin(check))
    return size, offset


def create_giant_head(head_size: bytes, size: int, offset: int):
    """ size + offset + check """
    head_offset = int_to_bytes(value=offset, length=4)
    xor = size ^ offset ^ 0xFFFFFFFF
    head_check = int_to_bytes(value=xor, length=4)
    return head_size + head_offset + head_check


class GiantQueue(CycledQueue):
    """
        Giant Data Queue
        ~~~~~~~~~~~~~~~~

        If data is too big (more than the whole buffer can load), it will be split to chunks,
        each chunk contains giant size, fragment offset & check (three 4 bytes integers, big-endian).

        The size of first chunk must be capacity - 4 (chunk size & its check took 4 bytes),
        and not greater than 65535, that will be the maximum size of each chunk too.
        So it means each fragment size will not greater than capacity - 16, or 65523.

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
    """
    MAX_CHUNK_SIZE = 65535

    def __init__(self, memory: Memory):
        super().__init__(memory=memory)
        # limit max size for each chunk
        max_size = self.capacity - 4  # deduct chunk size & its check (2 + 2 bytes)
        if max_size >= self.MAX_CHUNK_SIZE:
            self.__max_size = self.MAX_CHUNK_SIZE
        else:
            self.__max_size = max_size
        # receiving big data
        self.__incoming_giant_size = 0
        self.__incoming_giant_fragment = None
        # sending big data (split to chunks)
        self.__outgoing_giant_chunks: List[Union[bytes, bytearray]] = []

    def __check_package(self, body: Union[bytes, bytearray]) -> Union[bytes, bytearray, None]:
        """ check received package body without leading 2 bytes """
        body_size = len(body)
        if body_size < self.__max_size:
            # small package
            if self.__incoming_giant_fragment is None:
                # no previous chunks waiting to join,
                # so it must be a normal data package.
                return body
            # it's another chunk for giant
        # check chunk head, get giant size & offset
        assert body_size > 12, 'package size error: %s' % body
        giant_size, giant_offset = parse_giant_head(data=body[:12])
        if self.__incoming_giant_fragment is None:
            # first chunk for giant
            assert body_size == self.__max_size, 'first chunk size error: %d, %d' % (body_size, self.capacity)
            assert giant_size > (body_size - 12), 'giant size error: %d, body size: %d' % (giant_size, body_size)
            assert giant_offset == 0, 'first offset error: %d, size: %d' % (giant_offset, giant_size)
            self.__incoming_giant_size = giant_size
            self.__incoming_giant_fragment = body[12:]
        else:
            # another chunk for giant
            cache_size = len(self.__incoming_giant_fragment)
            assert giant_size == self.__incoming_giant_size, 'error: %d, %d' % (giant_size, self.__incoming_giant_size)
            assert giant_offset == cache_size, 'offset error: %d, %d, size: %d' % (giant_offset, cache_size, giant_size)
            cache_size += body_size - 12
            # check whether completed
            if cache_size < self.__incoming_giant_size:
                # not completed yet, cache this fragment
                self.__incoming_giant_fragment += body[12:]
            else:
                # giant completed (the sizes must be equal)
                giant = self.__incoming_giant_fragment + body[12:]
                self.__incoming_giant_fragment = None
                self.__incoming_giant_size = 0
                return giant

    # Override
    def shift(self) -> Union[bytes, bytearray, None]:
        """ remove data at front """
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

    # Override
    def push(self, data: Union[bytes, bytearray, None]) -> bool:
        """ append data to tail """
        # 1. check delay chunks for giant
        if not self.__check_chunks():
            # traffic jams
            return False
        # 2. check giant data
        if data is None:
            # do nothing
            return True
        elif len(data) < self.__max_size:
            # small data, send it directly
            return super().push(data=data)
        else:
            # giant data, split and send as chunks
            return self._push_giant(data=data)

    def _push_giant(self, data: Union[bytes, bytearray]) -> bool:
        self.__outgoing_giant_chunks = self.__split_giant(data=data)
        self.__check_chunks()
        return True

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
        fra_size = self.__max_size - 12  # deduct giant size (4 bytes), offset (4 bytes), and check (4 bytes)
        assert fra_size < data_size, 'data size error: %d < %d' % (data_size, fra_size)
        head_size = int_to_bytes(value=data_size, length=4)
        chunks = []
        p1 = 0
        while p1 < data_size:
            p2 = p1 + fra_size
            if p2 > data_size:
                p2 = data_size
            # size + offset + check + body
            head = create_giant_head(head_size=head_size, size=data_size, offset=p1)
            pack = head + data[p1:p2]
            chunks.append(pack)
            # next chunk
            p1 = p2
        return chunks
