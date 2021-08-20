# -*- coding: utf-8 -*-
#
#   STUN: Session Traversal Utilities for NAT
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

from typing import Union, Optional

from udp.ba import ByteArray, Data

from .header import MessageType, TransactionID, Header


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
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Package:
        if isinstance(data, cls):
            return data
        elif not isinstance(data, ByteArray):
            data = Data(buffer=data)
        # get STUN head
        head = Header.parse(data=data)
        if head is None:
            # not a STUN message?
            return None
        # check lengths
        head_len = head.size
        body_len = head.msg_length
        pack_len = head_len + body_len
        data_len = data.size
        if data_len < pack_len:
            # raise ValueError('STUN package length error: %d, %d' % (data_len, pack_len))
            return None
        elif data_len > pack_len:
            data = data.slice(start=0, end=pack_len)
        # get attributes body
        body = data.slice(start=head_len)
        return cls(data=data, head=head, body=body)

    @classmethod
    def new(cls, msg_type: MessageType, trans_id: Optional[TransactionID] = None,
            body: Union[bytes, bytearray, ByteArray] = None):
        if body is None:
            body = Data.ZERO
        elif not isinstance(body, ByteArray):
            body = Data(buffer=body)
        head = Header.new(msg_type=msg_type, msg_length=body.size, trans_id=trans_id)
        data = head.concat(body)
        return cls(data=data, head=head, body=body)
