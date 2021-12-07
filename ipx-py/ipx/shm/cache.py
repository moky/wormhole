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
from typing import Generic, Union, List

from .buffer import M
from .buffer import int_from_buffer, int_to_buffer
from .buffer import CycledBuffer


class CycledCache(CycledBuffer, Generic[M], ABC):
    """
        Cycled Data Cache
        ~~~~~~~~~~~~~~~~~

        Header:
            magic code             - 14 bytes
            offset of read offset  - 1 byte  # the highest bit is for alternate
            offset of write offset - 1 byte  # the highest bit is for alternate
            read offset            - 2/4/8 bytes
            alternate read offset  - 2/4/8 bytes
            write offset           - 2/4/8 bytes
            alternate write offset - 2/4/8 bytes
        Body:
            data package(s)        - data size (2 bytes) + data (variable length)
                                     the max size of data cannot greater than 65535,
                                     so each package cannot greater than 65537.

        Data package format:

             0                   1                   2                   3
             0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            |   package head (body size)    |     package body (payload)
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                package body (payload)                      ~
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        NOTICE: all integers are stored as NBO (Network Byte Order, big-endian)
    """

    def __init__(self, shm: M):
        super().__init__(shm=shm)
        # receiving big data
        self.__incoming_giant_size = 0
        self.__incoming_giant_fragment = None
        # sending big data (split to chunks)
        self.__outgoing_giant_chunks: List[Union[bytes, bytearray]] = []

    @abstractmethod
    def detach(self):
        """ Detaches the shared memory """
        raise NotImplemented

    @abstractmethod
    def remove(self):
        """ Removes (deletes) the shared memory from the system """
        raise NotImplemented

    @property
    def buffer(self) -> bytes:
        """ Gets the whole buffer """
        raise NotImplemented

    def _buffer_to_string(self) -> str:
        buffer = self.buffer
        size = len(buffer)
        if size < 128:
            return str(buffer)
        else:
            return str(buffer[:125]) + '...'

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        buffer = self._buffer_to_string()
        return '<%s size=%d capacity=%d available=%d>\n%s\n</%s module="%s">'\
               % (cname, self.size, self.capacity, self.available, buffer, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        buffer = self._buffer_to_string()
        return '<%s size=%d capacity=%d available=%d>\n%s\n</%s module="%s">'\
               % (cname, self.size, self.capacity, self.available, buffer, cname, mod)

    # Override
    def _try_read(self, length: int) -> (Union[bytes, bytearray, None], int):
        try:
            return super()._try_read(length=length)
        except AssertionError as error:
            self._check_error(error=error)
            # self.error(msg='failed to read data: %s' % error)
            # import traceback
            # traceback.print_exc()
            raise error

    def _read_package(self) -> Union[bytes, bytearray, None]:
        """
        Read one package, measured with size (as leading 2 bytes)

        :return: package body (without head)
        """
        # get data head as size
        head, _ = self._try_read(length=2)
        if head is None:
            return None
        body_size = int_from_buffer(buffer=head)
        pack_size = 2 + body_size
        available = self.available
        if available < pack_size:
            # data error, clear the whole buffer
            self.read(length=available)
            raise BufferError('buffer error: %d < 2 + %d' % (available, body_size))
        # get data body with size
        pack = self.read(length=pack_size)
        assert pack is not None and len(pack) == pack_size, 'package error: %d, %s' % (pack_size, pack)
        return pack[2:]

    def _write_package(self, body: Union[bytes, bytearray]) -> bool:
        """
        Write package with body size (as leading 2 bytes) into buffer

        :param body: package body
        :return: False on shared memory full
        """
        body_size = len(body)
        pack_size = 2 + body_size
        if self.spaces < pack_size:
            # not enough spaces
            return False
        head = int_to_buffer(value=body_size, length=2)
        if isinstance(body, bytearray):
            pack = bytearray(head) + body
        else:
            pack = bytearray(head + body)
        return self.write(data=pack)

    """
        Giant Data
        ~~~~~~~~~~
        
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
        giant_size = int_from_buffer(buffer=body[:4])
        giant_offset = int_from_buffer(buffer=body[4:8])
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

    def shift(self) -> Union[bytes, bytearray, None]:
        """ shift data """
        while True:
            body = self._read_package()
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
            if self._write_package(body=body):
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
        head_size = int_to_buffer(value=data_size, length=4)
        chunks = []
        p1 = 0
        while p1 < data_size:
            p2 = p1 + fra_size
            if p2 > data_size:
                p2 = data_size
            # size + offset + '\r\n' + body
            head_offset = int_to_buffer(value=p1, length=4)
            pack = head_size + head_offset + self.SEPARATOR + data[p1:p2]
            chunks.append(pack)
            # next chunk
            p1 = p2
        return chunks

    def append(self, data: Union[bytes, bytearray, None]) -> bool:
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
            return self._write_package(body=data)
        # 3. split giant, send as chunks
        return self._append_giant(data=data)

    def _append_giant(self, data: Union[bytes, bytearray]) -> bool:
        self.__outgoing_giant_chunks = self.__split_giant(data=data)
        self.__check_chunks()
        return True
