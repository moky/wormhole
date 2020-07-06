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
    [RFC] https://www.ietf.org/rfc/rfc3489.txt
"""

from typing import Optional

from udp.tlv import Data, MutableData, UInt16Data, UInt32Data
from udp.tlv import Tag, Length, Value, TagLengthValue

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


class AttributeType(UInt16Data, Tag):

    def __init__(self, value: int, data: Data=None, name: str=None):
        super().__init__(data=data, value=value)
        self.__name = name
        self.__attribute_types[value] = self

    def __str__(self):
        return self.__name

    def __repr__(self):
        return self.__name

    # Attribute Types in STUN message
    __attribute_types = {}  # int -> AttributeValue

    @classmethod
    def parse(cls, data: Data):
        if data.length < 2:
            return None
        elif data.length > 2:
            data = data.slice(end=2)
        value = data.get_uint16_value()
        t = cls.__attribute_types.get(value)
        if t is None:
            return cls(value=value, data=data)
        else:
            return t


# Comprehension-required range (0x0000-0x7FFF)
# Comprehension-optional range (0x8000-0xFFFF)

# [RFC-3489]
MappedAddress = AttributeType(value=0x0001, name='MAPPED-ADDRESS')
ResponseAddress = AttributeType(value=0x0002, name='RESPONSE-ADDRESS')
ChangeRequest = AttributeType(value=0x0003, name='CHANGE-REQUEST')
SourceAddress = AttributeType(value=0x0004, name='SOURCE-ADDRESS')
ChangedAddress = AttributeType(value=0x0005, name='CHANGED-ADDRESS')
Username = AttributeType(value=0x0006, name='USERNAME')
Password = AttributeType(value=0x0007, name='PASSWORD')
MessageIntegrity = AttributeType(value=0x0008, name='MESSAGE-INTEGRITY')
ErrorCode = AttributeType(value=0x0009, name='ERROR-CODE')
UnknownAttributes = AttributeType(value=0x000A, name='UNKNOWN-ATTRIBUTES')
ReflectedFrom = AttributeType(value=0x000B, name='REFLECTED-FROM')

# [RFC-5389]
Realm = AttributeType(0x0014, name='REALM')
Nonce = AttributeType(0x0015, name='NONCE')
XorMappedAddress = AttributeType(0x0020, name='XOR-MAPPED-ADDRESS(0020)')

XorMappedAddress2 = AttributeType(0x8020, name='XOR-MAPPED-ADDRESS(8020)')
XorOnly = AttributeType(0x8021, name='XOR-ONLY')
Software = AttributeType(0x8022, name='SOFTWARE')
AlternateServer = AttributeType(0x8023, name='ALTERNATE-SERVER')
Fingerprint = AttributeType(0x8028, name='FINGERPRINT')


class AttributeLength(UInt16Data, Length):

    @classmethod
    def parse(cls, data: Data, tag: AttributeType):
        length = super().parse(data=data, tag=tag)
        if length is not None:
            assert length.value & 0x0003 == 0, 'attribute length error: %d, %s' % (length.value, data)
            return length


class AttributeValue(Value):

    @classmethod
    def parse(cls, data: Data, tag: AttributeType, length: AttributeLength=None):  # -> AttributeValue:
        if data is None or data.length == 0:
            return None
        elif cls is AttributeValue:
            # get attribute parser with type
            clazz = cls.__value_classes.get(tag)
            if clazz is not None:
                # create instance by subclass
                return clazz.parse(data=data, tag=tag, length=length)
        return cls(data=data)

    #
    #   Runtime
    #
    __value_classes = {}  # tag -> class

    @classmethod
    def register(cls, tag: Tag, value_class):
        if value_class is None:
            cls.__value_classes.pop(tag)
        elif issubclass(value_class, AttributeValue):
            cls.__value_classes[tag] = value_class
        else:
            raise TypeError('%s must be subclass of AttributeValue' % value_class)


class Attribute(TagLengthValue):

    def __init__(self, data=None, tag: AttributeType=None, length: AttributeLength=None, value: AttributeValue=None):
        if data is None and length is None:
            if value is None:
                length = AttributeLength(value=0)
            else:
                length = AttributeLength(value=value.length)
        super().__init__(data=data, tag=tag, length=length, value=value)

    @classmethod
    def parse_tag(cls, data: Data) -> Optional[AttributeType]:
        return AttributeType.parse(data=data)

    @classmethod
    def parse_length(cls, data: Data, tag: AttributeType) -> Optional[AttributeLength]:
        return AttributeLength.parse(data=data, tag=tag)

    @classmethod
    def parse_value(cls, data: Data, tag: AttributeType, length: AttributeLength = None) -> Optional[Value]:
        return AttributeValue.parse(data=data, tag=tag, length=length)


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

    def __init__(self, data=None, ip: str=None, port: int=0, family: int=0):
        if data is None:
            assert ip is not None and port is not 0, 'IP:port error: (%s:%d' % (ip, port)
            if family is 0:
                family = self.family_ipv4
            if family == self.family_ipv4:
                # IPv4
                address = self.data_from_ipv4(ip=ip)
            else:
                # IPv6?
                address = None
            assert address is not None, 'failed to convert IP: %s, %d' % (ip, family)
            data = MutableData(capacity=8)
            data.append(0)
            data.append(family)
            data.append(UInt16Data(value=port))
            data.append(address)
        elif isinstance(data, MappedAddressValue):
            ip = data.ip
            port = data.port
            family = data.family
        super().__init__(data=data)
        self.__family = family
        self.__port = port
        self.__ip = ip

    def __str__(self):
        return '(%s:%d)' % (self.ip, self.port)

    def __repr__(self):
        return '(%s:%d)' % (self.ip, self.port)

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
    def data_from_ipv4(cls, ip: str) -> Data:
        # IPv4
        array = ip.split('.')
        assert len(array) == 4, 'IPv4 address error: %s' % ip
        data = MutableData(capacity=4)
        for i in range(4):
            data.append(int(array[i]))
        return data

    @classmethod
    def data_to_ipv4(cls, address: Data) -> str:
        # IPv4
        assert address.length == 4, 'IPv4 data error: %s' % address
        return '.'.join([
            str(address.get_byte(index=0)),
            str(address.get_byte(index=1)),
            str(address.get_byte(index=2)),
            str(address.get_byte(index=3)),
        ])

    @classmethod
    def parse(cls, data: Data, tag: AttributeType, length: AttributeLength=None):
        # checking head byte
        if data.get_byte(index=0) != 0:
            raise ValueError('mapped-address error: %s' % data)
        family = data.get_byte(index=1)
        if family == cls.family_ipv4:
            # IPv4
            if length.value == 8:
                port = data.get_uint16_value(2)
                ip = cls.data_to_ipv4(address=data.slice(start=4))
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

    def __init__(self, data=None, ip: str=None, port: int=0, family: int=0, factor: Data=None):
        if data is None:
            assert ip is not None and port is not 0, 'IP:port error: (%s:%d' % (ip, port)
            if family is 0:
                family = self.family_ipv4
            if family == self.family_ipv4:
                # IPv4
                address = self.data_from_ipv4(ip=ip)
            else:
                # IPv6?
                address = None
            assert address is not None, 'failed to convert IP: %s, %d' % (ip, family)
            data = MutableData(capacity=8)
            data.append(0)
            data.append(family)
            data.append(UInt16Data(value=port))
            data.append(address)
            assert factor is not None, 'xor factor empty'
            data = self.xor(data=data, factor=factor)
        super().__init__(data=data, ip=ip, port=port, family=family)

    @classmethod
    def xor(cls, data: Data, factor: Data) -> Optional[Data]:
        if data.get_byte(0) != 0:
            return None
        data_buffer = data._buffer
        data_offset = data._offset
        data_length = data._length
        fact_buffer = factor._buffer
        fact_offset = factor._offset
        fact_length = factor._length
        assert data_length == 8 or data_length == 20, 'address error: %s' % data
        assert fact_length == 16, 'factor should be the "magic code" + "(96-bits) transaction ID": %s' % factor
        array = bytearray(data_length)
        # family
        array[1] = data_buffer[data_offset+1]
        # X-Port
        array[2] = data_buffer[data_offset+2] ^ fact_buffer[fact_offset+1]
        array[3] = data_buffer[data_offset+3] ^ fact_buffer[fact_offset+0]
        # X-Address
        a_pos = data_length - 1
        f_pos = 0
        while a_pos >= 4:
            array[a_pos] = data_buffer[data_offset+a_pos] ^ fact_buffer[fact_offset+f_pos]
            a_pos -= 1
            f_pos += 1
        return Data(data=array)


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

    def __init__(self, data=None, ip: str=None, port: int=0, family: int=0, factor: Data=None):
        if data is None:
            assert ip is not None and port is not 0, 'IP:port error: (%s:%d' % (ip, port)
            if family is 0:
                family = self.family_ipv4
            if family == self.family_ipv4:
                # IPv4
                address = self.data_from_ipv4(ip=ip)
            else:
                # IPv6?
                address = None
            assert address is not None, 'failed to convert IP: %s, %d' % (ip, family)
            data = MutableData(capacity=8)
            data.append(0)
            data.append(family)
            data.append(UInt16Data(value=port))
            data.append(address)
            assert factor is not None, 'xor factor empty'
            data = self.xor(data=data, factor=factor)
        super().__init__(data=data, ip=ip, port=port, family=family)

    @classmethod
    def xor(cls, data: Data, factor: Data) -> Optional[Data]:
        if data.get_byte(0) != 0:
            return None
        data_buffer = data._buffer
        data_offset = data._offset
        data_length = data._length
        fact_buffer = factor._buffer
        fact_offset = factor._offset
        fact_length = factor._length
        assert data_length == 8 or data_length == 20, 'address error: %s' % data
        assert fact_length == 16, 'factor should be the "magic code" + "(96-bits) transaction ID": %s' % factor
        array = bytearray(data_length)
        # family
        array[1] = data_buffer[data_offset+1]
        # X-Port
        array[2] = data_buffer[data_offset+2] ^ fact_buffer[fact_offset+0]
        array[3] = data_buffer[data_offset+3] ^ fact_buffer[fact_offset+1]
        # X-Address
        a_pos = 4
        f_pos = 0
        while a_pos < data_length:
            array[a_pos] = data_buffer[data_offset+a_pos] ^ fact_buffer[fact_offset+f_pos]
            a_pos += 1
            f_pos += 1
        return Data(data=array)


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

    def __str__(self):
        return '%d' % self.value

    def __repr__(self):
        return '%d' % self.value

    @classmethod
    def parse(cls, data: Data, tag: Tag, length: Length=None):
        # check length
        if length.value != 4:
            raise ValueError('Change-Request value error: %s' % length)
        # get value
        value = data.get_uint32_value()
        if value == ChangeIPAndPort.value:
            return ChangeIPAndPort
        elif value == ChangeIP.value:
            return ChangeIP
        elif value == ChangePort.value:
            return ChangePort
        # else:
        #     # other values
        #     return ChangeRequestValue(value=value)


ChangeIP = ChangeRequestValue(value=0x00000004)
ChangePort = ChangeRequestValue(value=0x00000002)
ChangeIPAndPort = ChangeRequestValue(value=0x00000006)


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

    def __init__(self, description: str, data: Data=None):
        if data is None:
            data = description.encode('utf-8')
            length = len(data)
            tail = length & 3
            if tail > 0:
                length += 4 - tail
            mutable = MutableData(capacity=length)
            mutable.copy(index=0, source=data)
            if tail > 0:
                # set '\0' to fill the tail spaces
                length -= 1
                mutable.set_byte(index=length, value=0)
            data = mutable
        super().__init__(data=data)
        self.__desc = description

    def __str__(self):
        return self.__desc

    def __repr__(self):
        return self.__desc

    @property
    def description(self) -> str:
        return self.__desc

    @classmethod
    def parse(cls, data: Data, tag: Tag, length: Length=None):
        # get string
        desc = data.get_bytes().decode('utf-8').rstrip('\0')
        return cls(data=data, description=desc)


#
#  Register attribute parsers
#

AttributeValue.register(tag=MappedAddress, value_class=MappedAddressValue)
# AttributeValue.register(tag=XorMappedAddress, value_class=XorMappedAddressValue)
# AttributeValue.register(tag=XorMappedAddress2, value_class=XorMappedAddressValue2)

AttributeValue.register(tag=ResponseAddress, value_class=ResponseAddressValue)
AttributeValue.register(tag=ChangeRequest, value_class=ChangeRequestValue)
AttributeValue.register(tag=SourceAddress, value_class=SourceAddressValue)
AttributeValue.register(tag=ChangedAddress, value_class=ChangedAddressValue)

AttributeValue.register(tag=Software, value_class=SoftwareValue)
