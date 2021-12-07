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
            data item(s)           - data size (2 bytes) + data (variable length)
    """

    def __init__(self, shm: M):
        super().__init__(shm=shm)
        # receiving big data
        self.__incoming_giant_size = 0
        self.__incoming_giant_fragment = None
        # sending big data
        self.__outgoing_giant_chunks: List[Union[bytes, bytearray]] = []  # list of items

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

    def _shift_item(self) -> Union[bytes, bytearray, None]:
        """ shift one item, measured with size (as leading 2 bytes) """
        # get data head as size
        head, _ = self._try_read(length=2)
        if head is None:
            return None
        body_size = int_from_buffer(buffer=head)
        item_size = 2 + body_size
        available = self.available
        if available < item_size:
            # data error
            self.read(length=available)  # clear buffer
            raise BufferError('buffer error: %d < 2 + %d' % (available, body_size))
        # get data body with size
        item = self.read(length=item_size)
        if item is None:
            raise BufferError('failed to read item: %d' % item_size)
        return item[2:]

    def _append_item(self, body: Union[bytes, bytearray]) -> bool:
        """ append item with size (as leading 2 bytes) into buffer """
        body_size = len(body)
        item_size = 2 + body_size
        if self.spaces < item_size:
            # not enough spaces
            return False
        head = int_to_buffer(value=body_size, length=2)
        if isinstance(body, bytearray):
            item = bytearray(head) + body
        else:
            item = bytearray(head + body)
        return self.write(data=item)

    """
        Giant Data
        ~~~~~~~~~~
        
        If data is too big (more than the whole buffer can load), it will be
        split to chunks, each chunk contains giant size and it's offset
        (as two 4 bytes integer, big-endian).
        The item size for first chunk must be capacity - 2 (item size takes 2 bytes).
    """

    def __check_item(self, item: Union[bytes, bytearray]) -> Union[bytes, bytearray, None]:
        item_size = len(item)
        if (item_size + 2) < self.capacity:
            # small item
            if self.__incoming_giant_fragment is None:
                # normal data
                return item
            # it's another chunk for giant
        # else:
        #     # assert (item_size + 2) == self.capacity, 'first chunk error'
        #     assert self.__incoming_giant_fragment is None, 'first chunk error: %s' % item
        # check for big data
        assert item_size > 8, 'item size error: %s' % item
        giant_size = int_from_buffer(buffer=item[:4])
        giant_offset = int_from_buffer(buffer=item[4:8])
        if self.__incoming_giant_fragment is None:
            # first chunk for giant
            assert giant_size > (item_size - 8), 'giant size error: %d, item size: %d' % (giant_size, item_size)
            assert giant_offset == 0, 'first offset error: %d, size: %d' % (giant_offset, giant_size)
            self.__incoming_giant_size = giant_size
            self.__incoming_giant_fragment = item[8:]
        else:
            # another chunk for giant
            cache_size = len(self.__incoming_giant_fragment)
            expected_giant_size = self.__incoming_giant_size
            assert giant_size == expected_giant_size, 'giant size error: %d, %d' % (giant_size, expected_giant_size)
            assert giant_offset == cache_size, 'offset error: %d, %d, size: %d' % (giant_offset, cache_size, giant_size)
            cache_size += item_size - 8
            # check whether completed
            if cache_size >= expected_giant_size:
                # giant completed (the sizes must be equal)
                giant = self.__incoming_giant_fragment + item[8:]
                self.__incoming_giant_fragment = None
                return giant
            else:
                # not completed yet, cache this part
                self.__incoming_giant_fragment += item[8:]

    def shift(self) -> Union[bytes, bytearray, None]:
        """ shift data """
        while True:
            item = self._shift_item()
            if item is None:
                # no more item
                return None
            try:
                # check item for giant
                data = self.__check_item(item=item)
                if data is not None:
                    # complete data
                    return data
            except AssertionError as error:
                print('[SHM] giant error: %s' % error)
                # discard previous fragment
                self.__incoming_giant_size = 0
                self.__incoming_giant_fragment = None
                return item

    def __check_chunks(self) -> bool:
        chunks = self.__outgoing_giant_chunks.copy()
        for item in chunks:
            # send again
            if self._append_item(body=item):
                # item wrote
                self.__outgoing_giant_chunks.pop(0)
            else:
                # failed
                return False
        # all chunks flushed
        return True

    def __split_giant(self, data: Union[bytes, bytearray]) -> List[Union[bytes, bytearray]]:
        data_size = len(data)
        chunk_size = self.capacity - 10  # deduct item size (2 bytes), giant size and offset (4 + 4 bytes)
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
            item = head_size + head_offset + data[p1:p2]
            chunks.append(item)
            # next chunk
            p1 = p2
        return chunks

    def append(self, data: Union[bytes, bytearray]) -> bool:
        """ append data """
        # 1. check delay chunks for giant
        if not self.__check_chunks():
            return False
        # 2. check data
        data_size = len(data)
        if (data_size + 2) < self.capacity:
            # small data, send it directly
            return self._append_item(body=data)
        # 3. split giant, send as chunks
        return self._append_giant(data=data)

    def _append_giant(self, data: Union[bytes, bytearray]) -> bool:
        self.__outgoing_giant_chunks = self.__split_giant(data=data)
        self.__check_chunks()
        return True
