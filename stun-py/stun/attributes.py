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
    [RFC] https://www.ietf.org/rfc/rfc3489.txt
"""
from typing import Optional, Union

from .data import UInt16Data, UInt32Data
from .data import bytes_to_int
from .data import uint8_to_bytes, uint16_to_bytes
from .data import TLV, Type, Length, Value


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


class AttributeValue(Value):

    def __init__(self, data: Union[Value, bytes]):
        if isinstance(data, Value):
            data = data.data
        super().__init__(data=data)


class AttributeLength(UInt16Data, Length):
    pass


class AttributeType(UInt16Data, Type):

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2:
            return None
        elif data_len > 2:
            data = data[:2]
        return super().from_bytes(data=data)


# attribute types in STUN message
MappedAddress = AttributeType(0x0001)
ResponseAddress = AttributeType(0x0002)
ChangeRequest = AttributeType(0x0003)
SourceAddress = AttributeType(0x0004)
ChangedAddress = AttributeType(0x0005)
Username = AttributeType(0x0006)
Password = AttributeType(0x0007)
MessageIntegrity = AttributeType(0x0008)
ErrorCode = AttributeType(0x0009)
UnknownAttribute = AttributeType(0x000A)
ReflectedFrom = AttributeType(0x000B)

XorOnly = AttributeType(0x0021)
XorMappedAddress = AttributeType(0x8020)
ServerName = AttributeType(0x8022)
SecondaryAddress = AttributeType(0x8050)  # Non standard extension


class Attribute(TLV):

    def __init__(self, t: AttributeType, v: AttributeValue):
        l_data = uint16_to_bytes(len(v.data))
        data = t.data + l_data + v.data
        super().__init__(data=data, t=t, v=v)

    @classmethod
    def parse_type(cls, data: bytes) -> AttributeType:
        return AttributeType.parse(data=data)

    @classmethod
    def parse_length(cls, data: bytes, t: Type=None) -> AttributeLength:
        length = AttributeLength.parse(data=data)
        assert (length.value & 0x0003) == 0, 'attribute length error: %s' % data
        return length

    @classmethod
    def parse_value(cls, data: bytes, t: Type=None, length: Length=None) -> AttributeValue:
        if t == MappedAddress:
            return MappedAddressValue.parse(data=data)
        # other types
        value = super().parse_value(data=data, t=t, length=length)
        return AttributeValue(data=value)


"""
Rosenberg, et al.           Standards Track                    [Page 32]

RFC 5389                          STUN                      October 2008


   The format of the MAPPED-ADDRESS attribute is:

       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |0 0 0 0 0 0 0 0|    Family     |           Port                |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                                                               |
      |                 Address (32 bits or 128 bits)                 |
      |                                                               |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

               Figure 5: Format of MAPPED-ADDRESS Attribute

   The address family can take on the following values:

   0x01:IPv4
   0x02:IPv6

   The first 8 bits of the MAPPED-ADDRESS MUST be set to 0 and MUST be
   ignored by receivers.  These bits are present for aligning parameters
   on natural 32-bit boundaries.

   This attribute is used only by servers for achieving backwards
   compatibility with RFC 3489 [RFC3489] clients.
"""


class MappedAddressValue(AttributeValue):

    family_ipv4 = 0x01
    family_ipv6 = 0x02

    def __init__(self, data: bytes, ip: str, port: int, family: int):
        super().__init__(data=data)
        self.__family = family
        self.__port = port
        self.__ip = ip

    @property
    def family(self) -> int:
        return self.__family

    @property
    def port(self) -> int:
        return self.__port

    @property
    def ip(self) -> str:
        return self.__ip

    @classmethod
    def parse(cls, data: bytes):
        if data[0] != b'\0':
            return None
        family = bytes_to_int(data[1:2])
        port = bytes_to_int(data[2:4])
        address = data[4:]
        # check address family
        if family == cls.family_ipv4:
            assert len(address) == 4, 'IPv4 address error: %s' % address
            # IPv4
            ip = '.'.join([
                str(bytes_to_int(address[0:1])),
                str(bytes_to_int(address[1:2])),
                str(bytes_to_int(address[2:3])),
                str(bytes_to_int(address[3:4])),
            ])
        elif family == cls.family_ipv6:
            assert len(address) == 16, 'IPv6 address error: %s' % address
            # TODO: IPv6
            assert False, 'implement me!'
        else:
            raise ValueError('unknown address family: %d' % family)
        return cls(data=data, ip=ip, port=port, family=family)

    @classmethod
    def new(cls, ip: str, port: int, family: int=family_ipv4):
        if family == cls.family_ipv4:
            # IPv4
            array = ip.split('.')
            assert len(array) == 4, 'IP address error: %s' % ip
            address = bytes([int(x) for x in array])
            pass
        elif family == cls.family_ipv6:
            # TODO: IPv6
            assert False, 'implement me!'
        else:
            raise ValueError('unknown address family: %d' % family)
        data = b'\0' + uint8_to_bytes(family) + uint16_to_bytes(port) + address
        return cls(data=data, ip=ip, port=port, family=family)


"""
15.2.  XOR-MAPPED-ADDRESS

   The XOR-MAPPED-ADDRESS attribute is identical to the MAPPED-ADDRESS
   attribute, except that the reflexive transport address is obfuscated
   through the XOR function.

   The format of the XOR-MAPPED-ADDRESS is:

      0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |x x x x x x x x|    Family     |         X-Port                |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                X-Address (Variable)
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

             Figure 6: Format of XOR-MAPPED-ADDRESS Attribute
"""


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
    def xor(cls, data: bytes, factor: bytes) -> Optional[bytes]:
        if data[0] != b'\0':
            return None
        assert len(data) == 8 or len(data) == 20, 'address error: %s' % data
        assert len(factor) == 16, 'factor should be the "magic code" + "(96-bits) transaction ID"'
        array = bytearray(data)
        # X-Port
        array[2] ^= factor[1]
        array[3] ^= factor[0]
        # X-Address
        a_pos = len(array) - 1
        f_pos = 0
        while a_pos >= 4:
            array[a_pos] ^= factor[f_pos]
            a_pos -= 1
            f_pos += 1
        return array


"""
11.2.4 CHANGE-REQUEST

   The CHANGE-REQUEST attribute is used by the client to request that
   the server use a different address and/or port when sending the
   response.  The attribute is 32 bits long, although only two bits (A
   and B) are used:

    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 A B 0|
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

   The meaning of the flags is:

   A: This is the "change IP" flag.  If true, it requests the server
      to send the Binding Response with a different IP address than the
      one the Binding Request was received on.

   B: This is the "change port" flag.  If true, it requests the
      server to send the Binding Response with a different port than the
      one the Binding Request was received on.
"""


class ChangeRequestValue(UInt32Data, AttributeValue):

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 4:
            assert False, 'Change-Request value error: %s' % data
            # return None
        elif data_len > 4:
            data = data[:4]
        value = bytes_to_int(data)
        if value == ChangeIPAndPort.value:
            return ChangeIPAndPort
        elif value == ChangeIP.value:
            return ChangeIP
        elif value == ChangePort.value:
            return ChangePort
        # else:
        #     # other values
        #     return ChangeRequestValue(value=value)


ChangeIP = ChangeRequestValue(0x00000004)
ChangePort = ChangeRequestValue(0x00000002)
ChangeIPAndPort = ChangeRequestValue(0x00000006)
