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

from udp.tlv import Data, MutableData, UInt16Data

from .tlv import FieldName, FieldLength, FieldValue


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


class MappedAddressValue(FieldValue):
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
    def parse(cls, data: Data, tag: FieldName, length: FieldLength=None):
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
