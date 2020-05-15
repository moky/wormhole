# -*- coding: utf-8 -*-
#
#   STUN: Session Traversal Utilities for NAT
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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

from .data import Data, UInt16Data
from .data import random_bytes, uint32_to_bytes, bytes_to_int


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

    def __init__(self, value: int, data: bytes=None, name: str='Unknown Type'):
        super().__init__(value=value, data=data)
        self.__name = name
        s_message_types[value] = self

    def __str__(self):
        clazz = self.__class__.__name__
        return '<%s: %d "%s" />' % (clazz, self.value, self.__name)

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2 or (data[0] & 0xC0) != 0:
            # format: 00xx xxxx, xxxx xxxx
            return None
        elif data_len > 2:
            data = data[:2]
        value = bytes_to_int(data=data)
        t = s_message_types.get(value)
        if t is None:
            return cls(value=value, data=data)
        else:
            return t


# types for a STUN message
s_message_types = {}
BindRequest = MessageType(0x0001, name='BindRequest')
BindResponse = MessageType(0x0101, name='BindResponse')
BindErrorResponse = MessageType(0x0111, name='BindErrorResponse')
SharedSecretRequest = MessageType(0x0002, name='SharedSecretRequest')
SharedSecretResponse = MessageType(0x0102, name='SharedSecretResponse')
SharedSecretErrorResponse = MessageType(0x0112, name='SharedSecretErrorResponse')


class MessageLength(UInt16Data):

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2 or (data[1] & 0x03) != 0:
            # format: xxxx xxxx, xxxx xx00
            return None
        elif data_len > 2:
            data = data[:2]
        return super().from_bytes(data=data)


class TransactionID(Data):

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 16:
            return None
        elif data_len > 16:
            data = data[:16]
        assert data[:4] == MagicCookie, 'transaction ID not starts with magic cookie'
        return cls(data=data)

    @classmethod
    def new(cls):
        data = MagicCookie + random_bytes(12)
        return cls(data=data)


# Magic Cookie
MagicCookie = uint32_to_bytes(0x2112A442)


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


class Header:

    def __init__(self, data: bytes, msg_type: MessageType, msg_len: MessageLength, trans_id: TransactionID):
        super().__init__()
        self.__data = data
        self.__type = msg_type
        self.__length = msg_len
        self.__trans_id = trans_id

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def type(self) -> MessageType:
        return self.__type

    @property
    def length(self) -> MessageLength:
        return self.__length

    @property
    def trans_id(self) -> TransactionID:
        return self.__trans_id

    @classmethod
    def parse(cls, data: bytes):
        # get message type
        _type = MessageType.parse(data=data)
        if _type is None:
            return None
        else:
            data = data[_type.length:]
        # get message length
        _len = MessageLength.parse(data=data)
        if _len is None:
            return None
        else:
            data = data[_len.length:]
        # get transaction ID
        _id = TransactionID.parse(data=data)
        # build data
        data = _type.data + _len.data + _id.data
        return cls(data=data, msg_type=_type, msg_len=_len, trans_id=_id)

    @classmethod
    def new(cls, msg_type: MessageType, msg_len: MessageLength, trans_id: TransactionID=None):
        if trans_id is None:
            # generate Transaction ID
            trans_id = TransactionID.new()
        # build data
        data = msg_type.data + msg_len.data + trans_id.data
        return Header(data, msg_type, msg_len, trans_id)


class Package:

    def __init__(self, data: bytes, head: Header, body: bytes):
        super().__init__()
        self.__data = data
        assert head.length.value == len(body), 'STUN message length error: %d, %d' % (head.length.value, len(body))
        self.__head = head
        self.__body = body

    @property
    def data(self) -> bytes:
        if self.__data is None:
            head = self.head.data
            body = self.body
            self.__data = head + body
        return self.__data

    @property
    def head(self) -> Header:
        return self.__head

    @property
    def body(self) -> bytes:
        return self.__body

    @classmethod
    def parse(cls, data: bytes):
        # get STUN head
        head = Header.parse(data=data)
        if head is None:
            # not a STUN message?
            return None
        # check message length
        head_len = len(head.data)
        body_len = head.length.value
        if len(data) != (head_len + body_len):
            # raise ValueError('STUN message length error: %d, %d' % (body_len, len(data)))
            return None
        # get attributes body
        body = data[head_len:]
        return Package(data=data, head=head, body=body)

    @classmethod
    def new(cls, msg_type: MessageType, trans_id: TransactionID=None, body: bytes=b''):
        msg_len = MessageLength(len(body))
        head = Header.new(msg_type=msg_type, msg_len=msg_len, trans_id=trans_id)
        data = head.data + body
        return Package(data=data, head=head, body=body)
