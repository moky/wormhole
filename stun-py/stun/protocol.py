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

    RFC - https://www.ietf.org/rfc/rfc5389.txt
"""

import binascii
from enum import IntEnum
from typing import Union

import numpy


def bytes_to_int(data: bytes) -> int:
    return int.from_bytes(bytes=data, byteorder='big', signed=False)


def int_to_bytes(value: int, length) -> bytes:
    return value.to_bytes(length=length, byteorder='big', signed=False)


def uint8_to_bytes(value: int) -> bytes:
    return int_to_bytes(value=value, length=1)


def uint16_to_bytes(value: int) -> bytes:
    return int_to_bytes(value=value, length=2)


def uint32_to_bytes(value: int) -> bytes:
    return int_to_bytes(value=value, length=4)


def hex_decode(string: str) -> bytes:
    return binascii.a2b_hex(string)


def hex_to_int(hex_string: str) -> int:
    data = hex_decode(hex_string)
    return bytes_to_int(data)


"""
                        0                 1
                        2  3  4 5 6 7 8 9 0 1 2 3 4 5

                       +--+--+-+-+-+-+-+-+-+-+-+-+-+-+
                       |M |M |M|M|M|C|M|M|M|C|M|M|M|M|
                       |11|10|9|8|7|1|6|5|4|0|3|2|1|0|
                       +--+--+-+-+-+-+-+-+-+-+-+-+-+-+

                Figure 3: Format of STUN Message Type Field
"""


class MessageType:

    def __init__(self, data: Union[bytes, int]):
        super().__init__(self)
        if isinstance(data, bytes):
            assert len(data) == 2, 'STUN message type error: %s' % data
            self.__data = data
            self.__value = 0
        elif isinstance(data, int):
            self.__data = None
            self.__value = data

    def __eq__(self, other) -> bool:
        if isinstance(other, MessageType):
            return self.data == other.data
        if isinstance(other, bytes):
            return self.data == other
        if isinstance(other, int):
            return self.value == other

    @property
    def data(self) -> bytes:
        if self.__data is None:
            self.__data = uint16_to_bytes(self.__value)
        return self.__data

    @property
    def value(self) -> int:
        if self.__value is 0:
            self.__value = bytes_to_int(self.__data)
        return self.__value

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2 or (data[0] & 0xD0) != 0:
            return None
        if data_len > 2:
            data = data[:2]
        return MessageType(data)


# types for a STUN message
BindRequest = MessageType.parse(hex_decode('0001'))
BindResponse = MessageType.parse(hex_decode('0101'))
BindErrorResponse = MessageType.parse(hex_decode('0111'))
SharedSecretRequest = MessageType.parse(hex_decode('0002'))
SharedSecretResponse = MessageType.parse(hex_decode('0102'))
SharedSecretErrorResponse = MessageType.parse(hex_decode('0112'))


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
      |                                                               |
      |                     Transaction ID (96 bits)                  |
      |                                                               |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

                  Figure 2: Format of STUN Message Header

   The message length MUST contain the size, in bytes, of the message
   not including the 20-byte STUN header.  Since all STUN attributes are
   padded to a multiple of 4 bytes, the last 2 bits of this field are
   always zero.  This provides another way to distinguish STUN packets
   from packets of other protocols.
"""


# Magic Cookie
MagicCookie = uint32_to_bytes(0x2112A442)


class Header:

    def __init__(self, msg_type: MessageType, msg_len: int, trans_id: bytes):
        super().__init__(self)
        self.__data = None
        self.__type = msg_type
        self.__length = msg_len
        self.__id = trans_id

    @property
    def data(self) -> bytes:
        if self.__data is None:
            msg_type = self.type.data
            msg_len = uint16_to_bytes(self.length)
            trans_id = self.id
            self.__data = msg_type + msg_len + trans_id
        return self.__data

    @property
    def type(self) -> MessageType:
        return self.__type

    @property
    def length(self) -> int:
        return self.__length

    @property
    def id(self) -> bytes:
        return self.__id

    @classmethod
    def parse(cls, data: bytes):
        if len(data) < 20:
            return None
        # get STUN message type
        msg_type = MessageType.parse(data[0:2])
        if msg_type is None:
            return None
        # get STUN message length
        msg_len = bytes_to_int(data[2:4])
        if (msg_len & 0x0003) != 0:
            return None
        # get transaction ID
        trans_id = data[4:20]
        return Header(msg_type, msg_len, trans_id)

    @classmethod
    def new(cls, msg_type: MessageType, msg_len: int, trans_id: bytes=None):
        if trans_id is None:
            # generate Transaction ID
            trans_id = MagicCookie + bytes(numpy.random.bytes(12))
        return Header(msg_type, msg_len, trans_id)


class Package:

    def __init__(self, head: Header, body: bytes):
        super().__init__()
        self.__head = head
        self.__body = body
        self.__data = None

    @property
    def data(self) -> bytes:
        if self.__data is None:
            head = self.head.data
            body = self.body
            assert self.head.length == len(body), 'STUN message length error: %d, %d' % (self.head.length, len(body))
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
        if len(data) != (20 + head.length):
            # raise ValueError('STUN message length error: %d, %d' % (head.length, len(data)))
            return None
        # get attributes body
        body = data[20:]
        return Package(head=head, body=body)

    @classmethod
    def new(cls, msg_type: MessageType, trans_id: bytes=None, body: bytes=b''):
        body_len = len(body)
        head = Header.new(msg_type=msg_type, msg_len=body_len, trans_id=trans_id)
        return Package(head=head, body=body)


"""
    STUN Attributes
    ~~~~~~~~~~~~~~~
    
   After the STUN header are zero or more attributes.  Each attribute
   MUST be TLV encoded, with a 16-bit type, 16-bit length, and value.
   Each STUN attribute MUST end on a 32-bit boundary.  As mentioned
   above, all fields in an attribute are transmitted most significant
   bit first.

       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |         Type                  |            Length             |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Value (variable)                ....
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

                    Figure 4: Format of STUN Attributes
"""


# attribute types in STUN message
class AttributeType(IntEnum):

    MappedAddress = hex_to_int('0001')
    ResponseAddress = hex_to_int('0002')
    ChangeRequest = hex_to_int('0003')
    SourceAddress = hex_to_int('0004')
    ChangedAddress = hex_to_int('0005')
    Username = hex_to_int('0006')
    Password = hex_to_int('0007')
    MessageIntegrity = hex_to_int('0008')
    ErrorCode = hex_to_int('0009')
    UnknownAttribute = hex_to_int('000A')
    ReflectedFrom = hex_to_int('000B')

    XorOnly = hex_to_int('0021')
    XorMappedAddress = hex_to_int('8020')
    ServerName = hex_to_int('8022')
    SecondaryAddress = hex_to_int('8050')  # Non standard extension

    def __init__(self, x):
        super().__init__(x)
        self.__data = None

    @property
    def data(self) -> bytes:
        if self.__data is None:
            self.__data = uint16_to_bytes(self)
        return self.__data

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2:
            raise ValueError('attribute type error: %s' % data)
        if data_len > 2:
            data = data[:2]
        return bytes_to_int(data)


class Attribute:

    def __init__(self, attr_type: int, attr_len: int, attr_value: bytes):
        super().__init__(self)
        self.__type = attr_type
        self.__length = attr_len
        self.__value = attr_value
        self.__data = None

    @property
    def data(self) -> bytes:
        if self.__data is None:
            attr_type = uint16_to_bytes(self.type)
            attr_len = uint16_to_bytes(self.length)
            attr_value = self.value
            self.__data = attr_type + attr_len + attr_value
        return self.__data

    @property
    def type(self) -> int:
        return self.__type

    @property
    def length(self) -> int:
        return self.__length

    @property
    def value(self) -> bytes:
        return self.__value

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 4:
            return None
        attr_type = bytes_to_int(data[0:2])
        attr_len = bytes_to_int(data[2:4])
        assert attr_len & 0x0003 == 0, 'attribute length error: %d' % attr_len
        end = 4 + attr_len
        if data_len < end:
            return None
        attr_value = data_len[4:end]
        return Attribute(attr_type, attr_len, attr_value)


class MappedAddressValue:

    def __init__(self, family: int, port: int, address: Union[bytes, str]):
        super().__init__()
        self.__family = family
        self.__port = port
        # IP address
        if isinstance(address, bytes):
            self.__address = address
            self.__ip = None
        elif isinstance(address, str):
            self.__address = None
            self.__ip = address
        self.__data = None

    @property
    def data(self) -> bytes:
        if self.__data is None:
            family = uint8_to_bytes(self.family)
            port = uint16_to_bytes(self.port)
            address = self.address
            self.__data = family + port + address
        return self.__data

    @property
    def family(self) -> int:
        return self.__family

    @property
    def port(self) -> int:
        return self.__port

    @property
    def address(self) -> bytes:
        if self.__address is None:
            # TODO: convert IP string to Address bytes
            pass
        return self.__address

    @property
    def ip(self) -> str:
        if self.__ip is None:
            address = self.__address
            length = len(address)
            if length == 4:
                # IPv4
                ip = '.'.join([
                    str(bytes_to_int(address[0:1])),
                    str(bytes_to_int(address[1:2])),
                    str(bytes_to_int(address[2:3])),
                    str(bytes_to_int(address[3:4])),
                ])
                self.__ip = ip
            elif length == 16:
                # TODO: IPv6
                pass
        return self.__ip

    @classmethod
    def parse(cls, data: bytes):
        if data[0] != b'\0':
            return None
        family = bytes_to_int(data[1:2])
        port = bytes_to_int(data[2:4])
        address = data[4:]
        assert len(data) == 8 or len(data) == 20, 'address error: %s' % data
        return cls(family=family, port=port, address=address)


class XorMappedAddressValue(MappedAddressValue):

    """
    X-Port is computed by taking the mapped port in host byte order,
    XOR'ing it with the most significant 16 bits of the magic cookie, and
    then the converting the result to network byte order.  If the IP
    address family is IPv4, X-Address is computed by taking the mapped IP
    address in host byte order, XOR'ing it with the magic cookie, and
    converting the result to network byte order.  If the IP address
    family is IPv6, X-Address is computed by taking the mapped IP address
    in host byte order, XOR'ing it with the concatenation of the magic
    cookie and the 96-bit transaction ID, and converting the result to
    network byte order.
    """
    @classmethod
    def xor(cls, data: bytes, factor: bytes):
        if data[0] != b'\0':
            return None
        assert len(data) == 8 or len(data) == 20, 'address error: %s' % data
        assert len(factor) == 16, 'factor should be the "magic code" + "(96-bits) transaction ID"'
        # X-Port
        data[2] ^= factor[1]
        data[3] ^= factor[0]
        # X-Address
        a_pos = len(data) - 1
        f_pos = 0
        while a_pos >= 4:
            data[a_pos] ^= factor[f_pos]
            a_pos -= 1
            f_pos += 1
        return data
