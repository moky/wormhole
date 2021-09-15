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

from typing import Optional, Union

from udp.ba import ByteArray, Data, MutableData
from udp.ba import UInt32Data, Convert

from ..tlv import Tag
from ..tlv import Length
from ..tlv import ValueParser, RawValue

from .attributes import AttributeParser
from .attributes import AttributeType, AttributeLength, AttributeValue

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


class MappedAddressValue(RawValue):
    """
    15.1.  MAPPED-ADDRESS

        The MAPPED-ADDRESS attribute indicates a reflexive transport address
        of the client.  It consists of an 8-bit address family and a 16-bit
        port, followed by a fixed-length value representing the IP address.
        If the address family is IPv4, the address MUST be 32 bits.  If the
        address family is IPv6, the address MUST be 128 bits.  All fields
        must be in network byte order.
    """
    IPV4 = 0x01
    IPV6 = 0x02

    def __init__(self, data: Union[bytes, bytearray, ByteArray], ip: str, port: int, family: int):
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
    def data_from_ipv4(cls, ip: str) -> ByteArray:
        # IPv4
        array = ip.split('.')
        assert len(array) == 4, 'IPv4 address error: %s' % ip
        data = MutableData(capacity=4)
        for i in range(4):
            data.push(int(array[i]))
        return data

    @classmethod
    def data_to_ipv4(cls, address: ByteArray) -> str:
        # IPv4
        assert address.size == 4, 'IPv4 data error: %s' % address
        return '.'.join([
            str(address.get_byte(index=0)),
            str(address.get_byte(index=1)),
            str(address.get_byte(index=2)),
            str(address.get_byte(index=3)),
        ])

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[AttributeType] = None, length: Optional[AttributeLength] = None):
        if isinstance(data, cls):
            return data
        elif not isinstance(data, ByteArray):
            data = Data(buffer=data)
        # check length
        if length is not None and length.value < data.size:
            data = data.slice(start=0, end=length.value)
        # checking head byte
        if data.get_byte(index=0) != 0:
            raise ValueError('mapped-address error: %s' % data)
        family = data.get_byte(index=1)
        if family == cls.IPV4:
            if length.value == 8:
                port = Convert.int16_from_data(data=data, start=2)
                ip = cls.data_to_ipv4(address=data.slice(start=4))
                return cls(data=data, ip=ip, port=port, family=family)
        else:
            raise NotImplementedError('only IPV4 now')

    @classmethod
    def new_ipv4(cls, ip: str, port: int):
        family = cls.IPV4
        data = MutableData(capacity=8)
        data.push(0)
        data.push(family)
        data.append(Convert.uint16data_from_value(value=port))
        data.append(cls.data_from_ipv4(ip=ip))
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
    def xor(cls, data: ByteArray, factor: ByteArray) -> Optional[ByteArray]:
        if data.get_byte(0) != 0:
            return None
        data_buffer = data.buffer
        data_offset = data.offset
        data_length = data.size
        fact_buffer = factor.buffer
        fact_offset = factor.offset
        fact_length = factor.size
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
        return Data(buffer=array)


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
    def xor(cls, data: ByteArray, factor: ByteArray) -> Optional[ByteArray]:
        if data.get_byte(0) != 0:
            return None
        data_buffer = data.buffer
        data_offset = data.offset
        data_length = data.size
        fact_buffer = factor.buffer
        fact_offset = factor.offset
        fact_length = factor.size
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
        return Data(buffer=array)


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
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[AttributeType] = None, length: Optional[AttributeLength] = None):
        assert tag is not None, 'attribute type should not be empty'
        assert length.value == 4, 'Change-Request value error: %s' % length
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt32Data):
            data = Convert.uint32data_from_data(data=data)
        # get value
        value = data.value
        if value == cls.CHANGE_IP_AND_PORT.value:
            return cls.CHANGE_IP_AND_PORT
        elif value == cls.CHANGE_IP.value:
            return cls.CHANGE_IP
        elif value == cls.CHANGE_PORT.value:
            return cls.CHANGE_PORT
        # else:
        #     # other values
        #     return ChangeRequestValue(value=value)

    CHANGE_IP = None
    CHANGE_PORT = None
    CHANGE_IP_AND_PORT = None


def create_crv(value: int) -> ChangeRequestValue:
    ui16 = Convert.uint32data_from_value(value=value)
    return ChangeRequestValue(data=ui16, value=ui16.value, endian=ui16.endian)


ChangeRequestValue.CHANGE_IP = create_crv(value=0x00000004)
ChangeRequestValue.CHANGE_PORT = create_crv(value=0x00000002)
ChangeRequestValue.CHANGE_IP_AND_PORT = create_crv(value=0x00000006)


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


class SoftwareValue(RawValue):
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

    def __init__(self, data: Union[bytes, bytearray, ByteArray], description: str):
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
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[Tag] = None, length: Optional[Length] = None):  # -> SoftwareValue:
        if isinstance(data, cls):
            return data
        elif isinstance(data, ByteArray):
            data = data.get_bytes()
        desc = data.decode('utf-8').rstrip('\0')
        return cls(data=data, description=desc)

    @classmethod
    def new(cls, description: str):  # -> SoftwareValue:
        data = description.encode('utf-8')
        # set '\0' to fill the tail spaces
        tail = len(data) & 3
        if tail == 1:
            data += b'\0\0\0'
        elif tail == 2:
            data += b'\0\0'
        elif tail == 3:
            data += b'\0'
        return cls(data=data, description=description)


#
#  Attribute Value Parsers
#

class MappedAddressValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return MappedAddressValue.parse(data=data, tag=tag, length=length)


class ResponseAddressValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return ResponseAddressValue.parse(data=data, tag=tag, length=length)


class ChangeRequestValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return ChangeRequestValue.parse(data=data, tag=tag, length=length)


class SourceAddressValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return SourceAddressValue.parse(data=data, tag=tag, length=length)


class ChangedAddressValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return ChangedAddressValue.parse(data=data, tag=tag, length=length)


class SoftwareValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return SoftwareValue.parse(data=data, tag=tag, length=length)


#
#  Register Attribute Value parsers
#

AttributeParser.register(tag=AttributeType.MAPPED_ADDRESS, parser=MappedAddressValueParser())
# AttributeParser.register(tag=AttributeType.XOR_MAPPED_ADDRESS, parser=XorMappedAddressValueParser())
# AttributeParser.register(tag=AttributeType.XOR_MAPPED_ADDRESS2, parser=XorMappedAddressValue2Parser())

AttributeParser.register(tag=AttributeType.RESPONSE_ADDRESS, parser=ResponseAddressValueParser())
AttributeParser.register(tag=AttributeType.CHANGE_REQUEST, parser=ChangeRequestValueParser())
AttributeParser.register(tag=AttributeType.SOURCE_ADDRESS, parser=SourceAddressValueParser())
AttributeParser.register(tag=AttributeType.CHANGED_ADDRESS, parser=ChangedAddressValueParser())

AttributeParser.register(tag=AttributeType.SOFTWARE, parser=SoftwareValueParser())
