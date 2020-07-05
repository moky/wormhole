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

from ..attributes import AttributeType, AttributeValue
from ..attributes import XorMappedAddressValue


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
ChannelNumber = AttributeType(value=0x000C, name='CHANNEL-NUMBER')
Lifetime = AttributeType(value=0x000D, name='LIFETIME')
# BandWidth = AttributeType(value=0x0010, name='BANDWIDTH')  # Reserved
XorPeerAddress = AttributeType(value=0x0012, name='XOR-PEER-ADDRESS')
Data = AttributeType(value=0x0013, name='DATA')
XorRelayedAddress = AttributeType(value=0x0016, name='XOR-RELAYED-ADDRESS')
EvenPort = AttributeType(value=0x0018, name='EVEN-PORT')
RequestedTransport = AttributeType(value=0x0019, name='REQUESTED-TRANSPORT')
DontFragment = AttributeType(value=0x001A, name='DONT-FRAGMENT')
# TimerVal = AttributeType(value=0x0021, name='TIMER-VAL')   # Reserved
ReservationToken = AttributeType(value=0x0022, name='RESERVATION-TOKEN')

#
#  Register attribute parsers
#

AttributeValue.register(tag=XorPeerAddress, value_class=XorPeerAddressValue)
AttributeValue.register(tag=XorRelayedAddress, value_class=XorRelayedAddressValue)
