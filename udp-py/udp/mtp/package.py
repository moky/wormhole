# -*- coding: utf-8 -*-
#
#   MTP: Message Transfer Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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

from ..ba import ByteArray, Data

from .protocol import DataType, TransactionID
from .header import Header


class Package(Data):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], head: Header, body: ByteArray):
        if isinstance(data, ByteArray):
            super().__init__(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            super().__init__(buffer=data)
        self.__head = head
        self.__body = body

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: head=%s body_len=%d />' % (clazz, self.head, self.body.size)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: head=%s body_len=%d />' % (clazz, self.head, self.body.size)

    @property
    def head(self) -> Header:
        return self.__head

    @property
    def body(self) -> ByteArray:
        return self.__body

    @classmethod
    def parse(cls, data: ByteArray):  # -> Package
        # get package head
        head = Header.parse(data=data)
        if head is None:
            # raise AssertionError('package head error')
            return None
        # check lengths
        head_len = head.size
        body_len = head.body_length
        if body_len < 0:
            # UDP (unlimited)
            assert body_len == -1, 'body length error: %d' % body_len
        else:
            # TCP
            pack_len = head_len + body_len
            data_len = data.size
            if data_len < pack_len:
                # raise IndexError('package length error: %s' % data)
                return None
            elif data_len > pack_len:
                data = data.slice(start=0, end=pack_len)
        # get package body
        body = data.slice(start=head_len)
        return cls(data=data, head=head, body=body)

    @classmethod
    def new(cls, data_type: DataType, sn: TransactionID = None, pages: int = 1, index: int = 0, body_length: int = -1,
            body: ByteArray = None):
        # create package with header
        head = Header.new(data_type=data_type, sn=sn, pages=pages, index=index, body_length=body_length)
        if body is None:
            data = head
            body = Data.ZERO
        else:
            data = head.concat(body)
        return cls(data=data, head=head, body=body)
