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

from udp.mtp.data import Data, UInt16Data
from udp.mtp.data import random_bytes, bytes_to_int, uint16_to_bytes, uint32_to_bytes


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

    def __init__(self, value: int, data: bytes=None, name: str=None):
        if data is None:
            data = uint16_to_bytes(value)
        super().__init__(value=value, data=data)
        self.__name = name
        s_message_types[value] = self

    def __str__(self):
        # clazz = self.__class__.__name__
        if self.__name is None:
            return '"MessageType-0x%04X"' % self.value
        else:
            return '"%s"' % self.__name

    def __repr__(self):
        # clazz = self.__class__.__name__
        if self.__name is None:
            return '"MessageType-0x%04X"' % self.value
        else:
            return '"%s"' % self.__name

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
BindRequest = MessageType(0x0001, name='Binding Request')
BindResponse = MessageType(0x0101, name='Binding Response')
BindErrorResponse = MessageType(0x0111, name='Binding Error Response')
SharedSecretRequest = MessageType(0x0002, name='Shared Secret Request')
SharedSecretResponse = MessageType(0x0102, name='Shared Secret Response')
SharedSecretErrorResponse = MessageType(0x0112, name='Shared Secret Error Response')


class MessageLength(UInt16Data):

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = uint16_to_bytes(value)
        super().__init__(data=data, value=value)

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


class Header(Data):

    def __init__(self, data: bytes, msg_type: MessageType, msg_length: MessageLength, trans_id: TransactionID):
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
    def parse(cls, data: bytes):
        # get message type
        _type = MessageType.parse(data=data)
        if _type is None:
            return None
        pos = _type.length
        # get message length
        _len = MessageLength.parse(data=data[pos:])
        if _len is None:
            return None
        pos += _len.length
        # get transaction ID
        _id = TransactionID.parse(data=data[pos:])
        if _id is None:
            return None
        pos += _id.length
        assert pos == 20, 'header length error: %d' % pos
        if len(data) > pos:
            data = data[:pos]
        # create
        return cls(data=data, msg_type=_type, msg_length=_len, trans_id=_id)

    @classmethod
    def new(cls, msg_type: MessageType, msg_len: MessageLength, trans_id: TransactionID=None):
        if trans_id is None:
            # generate Transaction ID
            trans_id = TransactionID.new()
        # build data
        data = msg_type.data + msg_len.data + trans_id.data
        return Header(data=data, msg_type=msg_type, msg_length=msg_len, trans_id=trans_id)


class Package(Data):

    def __init__(self, data: bytes, head: Header, body: bytes):
        super().__init__(data=data)
        assert head.msg_length.value == len(body), 'STUN msg length error: %d, %d' % (head.msg_length.value, len(body))
        self.__head = head
        self.__body = body

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
        head_len = head.length
        body_len = head.msg_length.value
        pack_len = head_len + body_len
        data_len = len(data)
        if data_len < pack_len:
            # raise ValueError('STUN package length error: %d, %d' % (data_len, pack_len))
            return None
        elif data_len > pack_len:
            data = data[:pack_len]
        # get attributes body
        body = data[head_len:]
        return Package(data=data, head=head, body=body)

    @classmethod
    def new(cls, msg_type: MessageType, trans_id: TransactionID=None, body: bytes=b''):
        msg_len = MessageLength(len(body))
        head = Header.new(msg_type=msg_type, msg_len=msg_len, trans_id=trans_id)
        data = head.data + body
        return Package(data=data, head=head, body=body)
