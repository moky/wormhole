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

"""
    Session Traversal Utilities for NAT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    [RFC] https://www.ietf.org/rfc/rfc5389.txt
"""

import threading
from typing import Union

from dmtp.mtp.tlv.utils import random_bytes, bytes_to_int
from dmtp.mtp.tlv import Data, MutableData, UInt16Data, UInt32Data


"""
                        0                 1
                        2  3  4 5 6 7 8 9 0 1 2 3 4 5

                       +--+--+-+-+-+-+-+-+-+-+-+-+-+-+
                       |M |M |M|M|M|C|M|M|M|C|M|M|M|M|
                       |11|10|9|8|7|1|6|5|4|0|3|2|1|0|
                       +--+--+-+-+-+-+-+-+-+-+-+-+-+-+

                Figure 3: Format of STUN Message Type Field
"""


class MessageType(UInt16Data):

    def __init__(self, value: int, data: Union[Data, bytes, bytearray]=None, name: str=None):
        super().__init__(data=data, value=value)
        self.__name = name
        self.__message_types[value] = self

    def __str__(self):
        return self.__name

    def __repr__(self):
        return self.__name

    __message_types = {}  # int -> MessageType

    @classmethod
    def parse(cls, data: Data):
        if data.length < 2 or (data.get_byte(index=0) & 0xC0) != 0:
            # format: 00xx xxxx, xxxx xxxx
            return None
        elif data.length > 2:
            data = data.slice(end=2)
        value = data.get_uint16_value()
        t = cls.__message_types.get(value)
        if t is None:
            # name = 'MessageType-0x%04X' % value
            # t = cls(value=value, data=data, name=name)
            raise LookupError('msg type error: %d' % value)
        return t


# types for a STUN message
BindRequest = MessageType(0x0001, name='Binding Request')
BindResponse = MessageType(0x0101, name='Binding Response')
BindErrorResponse = MessageType(0x0111, name='Binding Error Response')
SharedSecretRequest = MessageType(0x0002, name='Shared Secret Request')
SharedSecretResponse = MessageType(0x0102, name='Shared Secret Response')
SharedSecretErrorResponse = MessageType(0x0112, name='Shared Secret Error Response')


class MessageLength(UInt16Data):

    @classmethod
    def parse(cls, data: Data):
        if data.length < 2 or (data.get_byte(index=1) & 0x03) != 0:
            # format: xxxx xxxx, xxxx xx00
            return None
        elif data.length > 2:
            data = data.slice(end=2)
        return cls(data=data)


class TransactionID(Data):

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: %s />' % (clazz, self._buffer)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: %s />' % (clazz, self._buffer)

    @classmethod
    def parse(cls, data: Data):
        if data.length < 16:
            # raise ValueError('transaction ID length error: %d' % data.length)
            return None
        elif data.length > 16:
            data = data.slice(end=16)
        # assert data.get_bytes(end=4) == MagicCookie, 'transaction ID not starts with magic cookie'
        return cls(data=data)

    __number_lock = threading.Lock()
    __number_hi = bytes_to_int(random_bytes(4))
    __number_mi = bytes_to_int(random_bytes(4))
    __number_lo = bytes_to_int(random_bytes(4))

    @classmethod
    def generate(cls):  # -> TransactionID:
        with cls.__number_lock:
            if cls.__number_lo < 0xFFFFFFFF:
                cls.__number_lo += 1
            else:
                cls.__number_lo = 0
                if cls.__number_mi < 0xFFFFFFFF:
                    cls.__number_mi += 1
                else:
                    cls.__number_mi = 0
                    if cls.__number_hi < 0xFFFFFFFF:
                        cls.__number_hi += 1
                    else:
                        cls.__number_hi = 0
            hi = UInt32Data(value=cls.__number_hi)
            mi = UInt32Data(value=cls.__number_mi)
            lo = UInt32Data(value=cls.__number_lo)
        data = MagicCookie.concat(hi).concat(mi).concat(lo)
        return cls(data=data)


# Magic Cookie
MagicCookie = UInt32Data(value=0x2112A442)


"""
    STUN Message Structure
    ~~~~~~~~~~~~~~~~~~~~~~

   STUN messages are encoded in binary using network-oriented format
   (most significant byte or octet first, also commonly known as big-
   endian).  The transmission order is described in detail in Appendix B
   of RFC 791 [RFC0791].  Unless otherwise noted, numeric constants are
   in decimal (base 10).

   All STUN messages MUST start with a 20-byte header followed by zero
   or more Attributes.  The STUN header contains a STUN message type,
   magic cookie, transaction ID, and message length.
   
       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |0 0|     STUN Message Type     |         Message Length        |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Magic Cookie                          |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                                                                
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                            Transaction ID (96 bits)                   
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                                                      |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

                  Figure 2: Format of STUN Message Header

   The message length MUST contain the size, in bytes, of the message
   not including the 20-byte STUN header.  Since all STUN attributes are
   padded to a multiple of 4 bytes, the last 2 bits of this field are
   always zero.  This provides another way to distinguish STUN packets
   from packets of other protocols.
"""


class Header(Data):

    def __init__(self, data=None,
                 msg_type: MessageType=None, msg_length: MessageLength=None, trans_id: TransactionID=None):
        if data is None:
            if trans_id is None:
                trans_id = TransactionID.generate()
            length = msg_type.length + msg_length.length + trans_id.length
            data = MutableData(capacity=length)
            data.append(msg_type)
            data.append(msg_length)
            data.append(trans_id)
        elif isinstance(data, Header):
            if msg_type is None:
                msg_type = data.type
            if msg_length is None:
                msg_length = data.msg_length
            if trans_id is None:
                trans_id = data.trans_id
        super().__init__(data=data)
        self.__type = msg_type
        self.__msg_length = msg_length
        self.__trans_id = trans_id

    @property
    def type(self) -> MessageType:
        return self.__type

    @property
    def msg_length(self) -> MessageLength:
        return self.__msg_length

    @property
    def trans_id(self) -> TransactionID:
        return self.__trans_id

    @classmethod
    def parse(cls, data: Data):
        # get message type
        _type = MessageType.parse(data=data)
        if _type is None:
            return None
        pos = _type.length
        # get message length
        _len = MessageLength.parse(data=data.slice(start=pos))
        if _len is None:
            return None
        pos += _len.length
        # get transaction ID
        _id = TransactionID.parse(data=data.slice(start=pos))
        if _id is None:
            return None
        pos += _id.length
        assert pos == 20, 'header length error: %d' % pos
        if data.length > pos:
            data = data.slice(end=pos)
        # create
        return cls(data=data, msg_type=_type, msg_length=_len, trans_id=_id)


class Package(Data):

    def __init__(self, data=None, head: Header=None, body: Data=None):
        if data is None:
            assert head is not None, 'package header should not empty'
            if body is None:
                body = Data.ZERO
                data = head
            else:
                data = head.concat(body)
        elif isinstance(data, Package):
            if head is None:
                head = data.head
            if body is None:
                body = data.body
        super().__init__(data=data)
        msg_length = head.msg_length.value
        assert msg_length == body.length, 'STUN msg length error: %d, %d' % (msg_length, body.length)
        self.__head = head
        self.__body = body

    @property
    def head(self) -> Header:
        return self.__head

    @property
    def body(self) -> bytes:
        return self.__body

    @classmethod
    def parse(cls, data: Data):
        # get STUN head
        head = Header.parse(data=data)
        if head is None:
            # not a STUN message?
            return None
        # check message length
        head_len = head.length
        pack_len = head_len + head.msg_length.value
        data_len = data.length
        if data_len < pack_len:
            # raise ValueError('STUN package length error: %d, %d' % (data_len, pack_len))
            return None
        elif data_len > pack_len:
            data = data.slice(end=pack_len)
        # get attributes body
        body = data.slice(start=head_len)
        return cls(data=data, head=head, body=body)

    @classmethod
    def new(cls, msg_type: MessageType, trans_id: TransactionID=None, body: Union[Data, bytes, bytearray]=None):
        if body is None:
            body = Data.ZERO
        elif not isinstance(body, Data):
            # bytes or bytearray
            body = Data(data=body)
        msg_len = MessageLength(value=body.length)
        head = Header(msg_type=msg_type, msg_length=msg_len, trans_id=trans_id)
        return cls(head=head, body=body)
