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
from typing import Optional

from udp.data import UInt16Data, UInt32Data
from udp.data import bytes_to_int, uint8_to_bytes, uint16_to_bytes, uint32_to_bytes
from udp.tlv import TLV, Type, Length, Value

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
    pass


class AttributeLength(UInt16Data, Length):

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = uint16_to_bytes(value)
        super().__init__(data=data, value=value)


class AttributeType(UInt16Data, Type):

    def __init__(self, value: int, data: bytes=None, name: str=None):
        if data is None:
            data = uint16_to_bytes(value)
        super().__init__(value=value, data=data)
        self.__name = name
        s_attribute_types[value] = self

    def __str__(self):
        # clazz = self.__class__.__name__
        if self.__name is None:
            return '"AttributeType-0x%04X"' % self.value
        else:
            return '"%s"' % self.__name

    def __repr__(self):
        # clazz = self.__class__.__name__
        if self.__name is None:
            return '"AttributeType-0x%04X"' % self.value
        else:
            return '"%s"' % self.__name

    def __hash__(self) -> int:
        return hash(self.value)

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 2:
            return None
        elif data_len > 2:
            data = data[:2]
        value = bytes_to_int(data=data)
        t = s_attribute_types.get(value)
        if t is None:
            return cls(value=value, data=data)
        else:
            return t


# Attribute Types in STUN message
s_attribute_types = {}

# Comprehension-required range (0x0000-0x7FFF)
# Comprehension-optional range (0x8000-0xFFFF)

# [RFC-3489]
MappedAddress = AttributeType(0x0001, name='MAPPED-ADDRESS')
ResponseAddress = AttributeType(0x0002, name='RESPONSE-ADDRESS')
ChangeRequest = AttributeType(0x0003, name='CHANGE-REQUEST')
SourceAddress = AttributeType(0x0004, name='SOURCE-ADDRESS')
ChangedAddress = AttributeType(0x0005, name='CHANGED-ADDRESS')
Username = AttributeType(0x0006, name='USERNAME')
Password = AttributeType(0x0007, name='PASSWORD')
MessageIntegrity = AttributeType(0x0008, name='MESSAGE-INTEGRITY')
ErrorCode = AttributeType(0x0009, name='ERROR-CODE')
UnknownAttributes = AttributeType(0x000A, name='UNKNOWN-ATTRIBUTES')
ReflectedFrom = AttributeType(0x000B, name='REFLECTED-FROM')

# [RFC-5389]
Realm = AttributeType(0x0014, name='REALM')
Nonce = AttributeType(0x0015, name='NONCE')
XorMappedAddress = AttributeType(0x0020, name='XOR-MAPPED-ADDRESS(0020)')

XorMappedAddress2 = AttributeType(0x8020, name='XOR-MAPPED-ADDRESS(8020)')
XorOnly = AttributeType(0x8021, name='XOR-ONLY')
Software = AttributeType(0x8022, name='SOFTWARE')
AlternateServer = AttributeType(0x8023, name='ALTERNATE-SERVER')
Fingerprint = AttributeType(0x8028, name='FINGERPRINT')


class Attribute(TLV):

    def __init__(self, t: AttributeType, v: AttributeValue, data: bytes=None):
        if data is None:
            data = t.data + uint16_to_bytes(len(v.data)) + v.data
        super().__init__(data=data, t=t, v=v)

    def __str__(self):
        clazz = self.__class__.__name__
        return '/* %s */ %s: %s' % (clazz, self.type, self.value)

    def __repr__(self):
        clazz = self.__class__.__name__
        return '/* %s */ %s: %s' % (clazz, self.type, self.value)

    @classmethod
    def parse_type(cls, data: bytes) -> Optional[AttributeType]:
        return AttributeType.parse(data=data)

    @classmethod
    def parse_length(cls, data: bytes, t: AttributeType) -> Optional[AttributeLength]:
        length = AttributeLength.parse(data=data, t=t)
        assert (length.value & 0x0003) == 0, 'attribute length error: %s' % data
        return length

    @classmethod
    def parse_value(cls, data: bytes, t: AttributeType, length: AttributeLength = None) -> Optional[Value]:
        if length is not None:
            # check length
            data_len = len(data)
            if data_len > length.value:
                data = data[:length.value]
            else:
                assert data_len == length.value, 'data length not enough: %d < %d' % (data_len, length.value)
        # get attribute parser with type
        parser = s_attribute_parsers.get(t)
        if parser is None:
            parser = AttributeValue
        return parser.parse(data=data, t=t, length=length)


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
    """
    15.1.  MAPPED-ADDRESS

        The MAPPED-ADDRESS attribute indicates a reflexive transport address
        of the client.  It consists of an 8-bit address family and a 16-bit
        port, followed by a fixed-length value representing the IP address.
        If the address family is IPv4, the address MUST be 32 bits.  If the
        address family is IPv6, the address MUST be 128 bits.  All fields
        must be in network byte order.
    """
    family_ipv4 = 0x01
    family_ipv6 = 0x02

    def __init__(self, data: bytes, ip: str, port: int, family: int):
        super().__init__(data=data)
        self.__family = family
        self.__port = port
        self.__ip = ip

    def __str__(self):
        return '"%s:%d"' % (self.ip, self.port)

    def __repr__(self):
        return '"%s:%d"' % (self.ip, self.port)

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
    def ip_to_bytes(cls, ip: str, family: int) -> bytes:
        if family == cls.family_ipv4:
            # IPv4
            array = ip.split('.')
            assert len(array) == 4, 'IP address error: %s' % ip
            return bytes([int(x) for x in array])
            pass
        elif family == cls.family_ipv6:
            # TODO: IPv6
            assert False, 'implement me!'
        else:
            raise ValueError('unknown address family: %d' % family)

    @classmethod
    def bytes_to_ip(cls, address: bytes, family: int) -> str:
        # check address family
        if family == cls.family_ipv4:
            assert len(address) == 4, 'IPv4 data error: %s' % address
            # IPv4
            return '.'.join([
                str(bytes_to_int(address[0:1])),
                str(bytes_to_int(address[1:2])),
                str(bytes_to_int(address[2:3])),
                str(bytes_to_int(address[3:4])),
            ])
        elif family == cls.family_ipv6:
            assert len(address) == 16, 'IPv6 data error: %s' % address
            # TODO: IPv6
            assert False, 'implement me!'
        else:
            raise ValueError('unknown address family: %d' % family)

    @classmethod
    def parse(cls, data: bytes, t: Type, length: Length=None):
        assert len(data) >= 8, 'mapped-address value error: %s' % data
        if data[0] != 0:
            return None
        family = bytes_to_int(data[1:2])
        port = bytes_to_int(data[2:4])
        ip = cls.bytes_to_ip(address=data[4:], family=family)
        return cls(data=data, ip=ip, port=port, family=family)

    @classmethod
    def new(cls, ip: str, port: int, family: int=None):
        if family is None:
            family = cls.family_ipv4
        address = cls.ip_to_bytes(ip=ip, family=family)
        data = b'\0' + uint8_to_bytes(family) + uint16_to_bytes(port) + address
        return cls(data=data, ip=ip, port=port, family=family)


"""
   The format of the XOR-MAPPED-ADDRESS is:

      0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |x x x x x x x x|    Family     |         X-Port                |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                X-Address (Variable)
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

             Figure 6: Format of XOR-MAPPED-ADDRESS Attribute

   The Family represents the IP address family, and is encoded
   identically to the Family in MAPPED-ADDRESS.


Rosenberg, et al.           Standards Track                    [Page 33]

RFC 5389                          STUN                      October 2008
"""


class XorMappedAddressValue(MappedAddressValue):
    """
    15.2.  XOR-MAPPED-ADDRESS

        The XOR-MAPPED-ADDRESS attribute is identical to the MAPPED-ADDRESS
        attribute, except that the reflexive transport address is obfuscated
        through the XOR function.

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

        The rules for encoding and processing the first 8 bits of the
        attribute's value, the rules for handling multiple occurrences of the
        attribute, and the rules for processing address families are the same
        as for MAPPED-ADDRESS.

        Note: XOR-MAPPED-ADDRESS and MAPPED-ADDRESS differ only in their
        encoding of the transport address.  The former encodes the transport
        address by exclusive-or'ing it with the magic cookie.  The latter
        encodes it directly in binary.  RFC 3489 originally specified only
        MAPPED-ADDRESS.  However, deployment experience found that some NATs
        rewrite the 32-bit binary payloads containing the NAT's public IP
        address, such as STUN's MAPPED-ADDRESS attribute, in the well-meaning
        but misguided attempt at providing a generic ALG function.  Such
        behavior interferes with the operation of STUN and also causes
        failure of STUN's message-integrity checking.
    """

    @classmethod
    def xor(cls, data: bytes, factor: bytes) -> Optional[bytes]:
        if data[0] != 0:
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
        return bytes(array)

    @classmethod
    def new(cls, ip: str, port: int, family: int=None, factor: bytes=None):
        if family is None:
            family = cls.family_ipv4
        address = cls.ip_to_bytes(ip=ip, family=family)
        data = b'\0' + uint8_to_bytes(family) + uint16_to_bytes(port) + address
        assert factor is not None, 'missing factor'
        data = cls.xor(data=data, factor=factor)
        return cls(data=data, ip=ip, port=port, family=family)


class XorMappedAddressValue2(MappedAddressValue):
    """ https://tools.ietf.org/id/draft-ietf-behave-rfc3489bis-02.txt

    10.2.12  XOR-MAPPED-ADDRESS

        The XOR-MAPPED-ADDRESS attribute is only present in Binding
        Responses.  It provides the same information that is present in the
        MAPPED-ADDRESS attribute.  However, the information is encoded by

        performing an exclusive or (XOR) operation between the mapped address
        and the transaction ID.  Unfortunately, some NAT devices have been
        found to rewrite binary encoded IP addresses and ports that are
        present in protocol payloads.  This behavior interferes with the
        operation of STUN.  By providing the mapped address in an obfuscated
        form, STUN can continue to operate through these devices.

        The format of the XOR-MAPPED-ADDRESS is:

        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |x x x x x x x x|    Family     |         X-Port                |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                X-Address (Variable)
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        The Family represents the IP address family, and is encoded
        identically to the Family in MAPPED-ADDRESS.

        X-Port is equal to the port in MAPPED-ADDRESS, exclusive or'ed with
        most significant 16 bits of the transaction ID.  If the IP address
        family is IPv4, X-Address is equal to the IP address in MAPPED-
        ADDRESS, exclusive or'ed with the most significant 32 bits of the
        transaction ID.  If the IP address family is IPv6, the X-Address is
        equal to the IP address in MAPPED-ADDRESS, exclusive or'ed with the
        entire 128 bit transaction ID.
    """

    @classmethod
    def xor(cls, data: bytes, factor: bytes) -> Optional[bytes]:
        if data[0] != 0:
            return None
        assert len(data) == 8 or len(data) == 20, 'address error: %s' % data
        assert len(factor) == 16, 'factor should be the "magic code" + "(96-bits) transaction ID"'
        array = bytearray(data)
        # X-Port
        array[2] ^= factor[0]
        array[3] ^= factor[1]
        # X-Address
        length = len(array)
        a_pos = 4
        f_pos = 0
        while a_pos < length:
            array[a_pos] ^= factor[f_pos]
            a_pos += 1
            f_pos += 1
        return bytes(array)

    @classmethod
    def new(cls, ip: str, port: int, family: int=None, factor: bytes=None):
        if family is None:
            family = cls.family_ipv4
        address = cls.ip_to_bytes(ip=ip, family=family)
        data = b'\0' + uint8_to_bytes(family) + uint16_to_bytes(port) + address
        assert factor is not None, 'missing factor'
        data = cls.xor(data=data, factor=factor)
        return cls(data=data, ip=ip, port=port, family=family)


class ResponseAddressValue(MappedAddressValue):
    """
    11.2.2 RESPONSE-ADDRESS

        The RESPONSE-ADDRESS attribute indicates where the response to a
        Binding Request should be sent.  Its syntax is identical to MAPPED-
        ADDRESS.

    (Defined in RFC-3489, removed from RFC-5389)
    """
    pass


class ChangedAddressValue(MappedAddressValue):
    """
    11.2.3  CHANGED-ADDRESS

        The CHANGED-ADDRESS attribute indicates the IP address and port where
        responses would have been sent from if the "change IP" and "change
        port" flags had been set in the CHANGE-REQUEST attribute of the
        Binding Request.  The attribute is always present in a Binding
        Response, independent of the value of the flags.  Its syntax is
        identical to MAPPED-ADDRESS.

    (Defined in RFC-3489, removed from RFC-5389)
    """
    pass


class ChangeRequestValue(UInt32Data, AttributeValue):
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

    (Defined in RFC-3489, removed from RFC-5389)
    """

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = uint32_to_bytes(value)
        super().__init__(data=data, value=value)

    def __str__(self):
        return '%d' % self.value

    def __repr__(self):
        return '%d' % self.value

    @classmethod
    def parse(cls, data: bytes, t: Type, length: Length=None):
        assert length.value == 4, 'Change-Request value error: %s' % length
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


class SourceAddressValue(MappedAddressValue):
    """
    11.2.5 SOURCE-ADDRESS

        The SOURCE-ADDRESS attribute is present in Binding Responses.  It
        indicates the source IP address and port that the server is sending
        the response from.  Its syntax is identical to that of MAPPED-
        ADDRESS.

    (Defined in RFC-3489, removed from RFC-5389)
    """
    pass


class SoftwareValue(AttributeValue):
    """
    15.10.  SOFTWARE

        The SOFTWARE attribute contains a textual description of the software
        being used by the agent sending the message.  It is used by clients
        and servers.  Its value SHOULD include manufacturer and version
        number.  The attribute has no impact on operation of the protocol,
        and serves only as a tool for diagnostic and debugging purposes.  The
        value of SOFTWARE is variable length.  It MUST be a UTF-8 [RFC3629]
        encoded sequence of less than 128 characters (which can be as long as
        763 bytes).
    """

    def __init__(self, data: bytes, description: str):
        super().__init__(data=data)
        self.__desc = description

    def __str__(self):
        return '"%s"' % self.__desc

    def __repr__(self):
        return '"%s"' % self.__desc

    @property
    def description(self) -> str:
        return self.__desc

    @classmethod
    def parse(cls, data: bytes, t: Type, length: Length=None):
        if length is None or length.value == 0:
            return None
        else:
            length = length.value
        data_len = len(data)
        if data_len < length:
            return None
        elif data_len > length:
            data = data[:length]
        desc = data.rstrip(b'\0').decode('utf-8')
        return cls(data=data, description=desc)

    @classmethod
    def new(cls, description: str):
        data = description.encode('utf-8')
        # padding with '\0'
        length = len(data)
        tail = length & 3
        while tail < 4:
            data += b'\0'
            tail += 1
        return cls(data=data, description=description)


#
#  Register attribute parsers
#
s_attribute_parsers = {
    MappedAddress: MappedAddressValue,
    # XorMappedAddress: XorMappedAddressValue,
    # XorMappedAddress2: XorMappedAddressValue2,

    ResponseAddress: ResponseAddressValue,
    ChangeRequest: ChangeRequestValue,
    SourceAddress: SourceAddressValue,
    ChangedAddress: ChangedAddressValue,

    Software: SoftwareValue,
}
