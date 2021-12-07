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
        """ read one package, measured with size (as leading 2 bytes) """
        # get data head as size
        head, _ = self._try_read(length=2)
        if head is None:
            return None
        body_size = int_from_buffer(buffer=head)
        pack_size = 2 + body_size
        available = self.available
        if available < pack_size:
            # data error
            self.read(length=available)  # clear buffer
            raise BufferError('buffer error: %d < 2 + %d' % (available, body_size))
        # get data body with size
        pack = self.read(length=pack_size)
        if pack is None:
            raise BufferError('failed to read package: %d' % pack_size)
        # return payload without head
        return pack[2:]

    def _write_package(self, body: Union[bytes, bytearray]) -> bool:
        """ write package with body size (as leading 2 bytes) into buffer """
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
        
        If data is too big (more than the whole buffer can load), it will be
        split to chunks, each chunk contains giant size and it's offset
        (as two 4 bytes integer, big-endian).
        The size of first chunk must be capacity - 2 (chunk size takes 2 bytes).
    """

    def __check_package(self, pack: Union[bytes, bytearray]) -> Union[bytes, bytearray, None]:
        pack_size = len(pack)
        if (pack_size + 2) < self.capacity:
            # small package
            if self.__incoming_giant_fragment is None:
                # no previous chunks waiting to join,
                # so it must be a normal data package.
                return pack
            # it's another chunk for giant
        # else:
        #     # assert (pack_size + 2) == self.capacity, 'first chunk error'
        #     assert self.__incoming_giant_fragment is None, 'first chunk error: %s' % pack
        # check for big data
        assert pack_size > 8, 'package size error: %s' % pack
        giant_size = int_from_buffer(buffer=pack[:4])
        giant_offset = int_from_buffer(buffer=pack[4:8])
        if self.__incoming_giant_fragment is None:
            # first chunk for giant
            assert giant_size > (pack_size - 8), 'giant size error: %d, package size: %d' % (giant_size, pack_size)
            assert giant_offset == 0, 'first offset error: %d, size: %d' % (giant_offset, giant_size)
            self.__incoming_giant_size = giant_size
            self.__incoming_giant_fragment = pack[8:]
        else:
            # another chunk for giant
            cache_size = len(self.__incoming_giant_fragment)
            expected_giant_size = self.__incoming_giant_size
            assert giant_size == expected_giant_size, 'giant size error: %d, %d' % (giant_size, expected_giant_size)
            assert giant_offset == cache_size, 'offset error: %d, %d, size: %d' % (giant_offset, cache_size, giant_size)
            cache_size += pack_size - 8
            # check whether completed
            if cache_size >= expected_giant_size:
                # giant completed (the sizes must be equal)
                giant = self.__incoming_giant_fragment + pack[8:]
                self.__incoming_giant_fragment = None
                return giant
            else:
                # not completed yet, cache this part
                self.__incoming_giant_fragment += pack[8:]

    def shift(self) -> Union[bytes, bytearray, None]:
        """ shift data """
        while True:
            pack = self._read_package()
            if pack is None:
                # no more packages
                return None
            try:
                # check pack for giant
                data = self.__check_package(pack=pack)
                if data is not None:
                    # complete data
                    return data
            except AssertionError as error:
                print('[SHM] giant error: %s' % error)
                # discard previous fragment
                self.__incoming_giant_size = 0
                self.__incoming_giant_fragment = None
                # return current package to application
                return pack

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
        chunk_size = self.capacity - 10  # deduct chunk size (2 bytes), giant size and offset (4 + 4 bytes)
        assert chunk_size < data_size, 'data size error: %d < %d' % (data_size, chunk_size)
        head_size = int_to_buffer(value=data_size, length=4)
        chunks = []
        p1 = 0
        while p1 < data_size:
            p2 = p1 + chunk_size
            if p2 > data_size:
                p2 = data_size
            # size + offset + body
            head_offset = int_to_buffer(value=p1, length=4)
            pack = head_size + head_offset + data[p1:p2]
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
        if (data_size + 2) < self.capacity:
            # small data, send it directly
            return self._write_package(body=data)
        # 3. split giant, send as chunks
        return self._append_giant(data=data)

    def _append_giant(self, data: Union[bytes, bytearray]) -> bool:
        self.__outgoing_giant_chunks = self.__split_giant(data=data)
        self.__check_chunks()
        return True
