# -*- coding: utf-8 -*-
#
#   TURN: Traversal Using Relays around NAT
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
    Traversal Using Relays around NAT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    [RFC] https://www.ietf.org/rfc/rfc5766.txt
"""

from typing import Optional

from udp.ba import ByteArray

from ..tlv import ValueParser

from ..protocol.attributes import create_type
from ..protocol import AttributeParser
from ..protocol import AttributeType, AttributeLength, AttributeValue
from ..protocol import XorMappedAddressValue


class XorPeerAddressValue(XorMappedAddressValue):
    """
    14.3.  XOR-PEER-ADDRESS

        The XOR-PEER-ADDRESS specifies the address and port of the peer as
        seen from the TURN server.  (For example, the peer's server-reflexive
        transport address if the peer is behind a NAT.)  It is encoded in the
        same way as XOR-MAPPED-ADDRESS [RFC5389].
    """
    pass


class XorRelayedAddressValue(XorMappedAddressValue):
    """
    14.5.  XOR-RELAYED-ADDRESS

        The XOR-RELAYED-ADDRESS is present in Allocate responses.  It
        specifies the address and port that the server allocated to the
        client.  It is encoded in the same way as XOR-MAPPED-ADDRESS
        [RFC5389].
    """
    pass


# New STUN Attributes
AttributeType.CHANNEL_NUMBER = create_type(value=0x000C, name='CHANNEL-NUMBER')
AttributeType.LIFETIME = create_type(value=0x000D, name='LIFETIME')
# AttributeType.BANDWIDTH = create_type(value=0x0010, name='BANDWIDTH')  # Reserved
AttributeType.XOR_PEER_ADDRESS = create_type(value=0x0012, name='XOR-PEER-ADDRESS')
AttributeType.DATA = create_type(value=0x0013, name='DATA')
AttributeType.XOR_RELAYED_ADDRESS = create_type(value=0x0016, name='XOR-RELAYED-ADDRESS')
AttributeType.EVEN_PORT = create_type(value=0x0018, name='EVEN-PORT')
AttributeType.REQUESTED_TRANSPORT = create_type(value=0x0019, name='REQUESTED-TRANSPORT')
AttributeType.DONT_FRAGMENT = create_type(value=0x001A, name='DONT-FRAGMENT')
# AttributeType.TIMER_VAL = create_type(value=0x0021, name='TIMER-VAL')   # Reserved
AttributeType.RESERVATION_TOKEN = create_type(value=0x0022, name='RESERVATION-TOKEN')


#
#  Attribute Value Parsers
#

class XorPeerAddressValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return XorPeerAddressValue.parse(data=data, tag=tag, length=length)


class XorRelayedAddressValueParser(ValueParser[AttributeType, AttributeLength, AttributeValue]):

    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        return XorRelayedAddressValue.parse(data=data, tag=tag, length=length)


#
#  Register Attribute Value Parsers
#

AttributeParser.register(tag=AttributeType.XOR_PEER_ADDRESS, parser=XorPeerAddressValueParser())
AttributeParser.register(tag=AttributeType.XOR_RELAYED_ADDRESS, parser=XorRelayedAddressValueParser())
