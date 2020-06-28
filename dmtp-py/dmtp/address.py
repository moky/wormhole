# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
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

from udp.tlv import Tag, Value, Length
from udp.tlv.data import bytes_to_int, uint8_to_bytes, uint16_to_bytes


"""
    Address Values
    ~~~~~~~~~~~~~~


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

    The address family can take on the following values:

    0x01:IPv4
    0x02:IPv6

    The first 8 bits of the MAPPED-ADDRESS MUST be set to 0 and MUST be
    ignored by receivers.  These bits are present for aligning parameters
    on natural 32-bit boundaries.
"""


class MappedAddressValue(Value):
    """
        MAPPED-ADDRESS
        ~~~~~~~~~~~~~~

        The MAPPED-ADDRESS attribute indicates a reflexive transport address
        of the client.  It consists of an 8-bit address family and a 16-bit
        port, followed by a fixed-length value representing the IP address.
        If the address family is IPv4, the address MUST be 32 bits.  If the
        address family is IPv6, the address MUST be 128 bits.  All fields
        must be in network byte order.
    """
    family_ipv4 = 0x01
    family_ipv6 = 0x02

    def __init__(self, ip: str, port: int, family: int = 0x01, data: bytes = None):
        if data is None:
            ip_data = self.ip_to_bytes(ip=ip, family=family)
            port_data = uint16_to_bytes(value=port)
            family_data = uint8_to_bytes(value=family)
            data = b'\0' + family_data + port_data + ip_data
        super().__init__(data=data)
        self.__ip = ip
        self.__port = port

    def __str__(self):
        return '"%s:%d"' % (self.ip, self.port)

    def __repr__(self):
        return '"%s:%d"' % (self.ip, self.port)

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def port(self) -> int:
        return self.__port

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
    def parse(cls, data: bytes, tag: Tag, length: Length = None):
        assert len(data) >= 8, 'mapped-address value error: %s' % data
        if data[0] != 0:
            return None
        family = bytes_to_int(data[1:2])
        port = bytes_to_int(data[2:4])
        ip = cls.bytes_to_ip(address=data[4:], family=family)
        return cls(data=data, ip=ip, port=port, family=family)


class SourceAddressValue(MappedAddressValue):
    """
        SOURCE-ADDRESS
        ~~~~~~~~~~~~~~

        The SOURCE-ADDRESS attribute is present in Binding Responses.  It
        indicates the source IP address and port that the server is sending
        the response from.  Its syntax is identical to that of MAPPED-
        ADDRESS.
    """
    pass


class RelayedAddressValue(MappedAddressValue):
    """
        RELAYED-ADDRESS
        ~~~~~~~~~~~~~~~

        The RELAYED-ADDRESS attribute is present in Allocate responses.  It
        specifies the address and port that the server allocated to the
        client.  It is encoded in the same way as MAPPED-ADDRESS.
    """
    pass
