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
from .queue import Queue
from .buffer import CycledBuffer


class CycledQueue(CycledBuffer, Queue):
    """
        Cycled Data Queue
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

    # Override
    def shift(self) -> Union[bytes, bytearray, None]:
        """
        Get one package, measured with size (as leading 2 bytes)

        :return: package body (without head)
        """
        # get data head as size
        head = self.peek(length=2)
        if head is None:
            return None
        body_size = int_from_bytes(data=head)
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

    # Override
    def push(self, data: Union[bytes, bytearray]) -> bool:
        """
        Put package with body size (as leading 2 bytes) into buffer

        :param data: package body
        :return: False on shared memory full
        """
        body_size = len(data)
        pack_size = 2 + body_size
        if self.spaces < pack_size:
            # not enough spaces
            return False
        head = int_to_bytes(value=body_size, length=2)
        if isinstance(data, bytearray):
            pack = bytearray(head) + data
        else:
            pack = bytearray(head + data)
        return self.write(data=pack)
