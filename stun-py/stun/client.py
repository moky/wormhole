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

    Client node
"""

from abc import ABC
from typing import Optional

from udp.tlv import Data

from .protocol import Package
from .protocol import BindRequest, BindResponse
from .attributes import Attribute, AttributeType, AttributeLength, AttributeValue
from .attributes import ChangePort, ChangeIPAndPort
from .attributes import ChangeRequest
from .attributes import MappedAddress, MappedAddressValue
from .attributes import XorMappedAddress, XorMappedAddressValue
from .attributes import XorMappedAddress2, XorMappedAddressValue2
from .attributes import SourceAddress, SourceAddressValue
from .attributes import ChangedAddress, ChangedAddressValue
from .attributes import Software, SoftwareValue
from .node import Node, NatType


class Client(Node, ABC):

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.retries = 3

    def parse_attribute(self, attribute: Attribute, context: dict) -> bool:
        tag = attribute.tag
        value = attribute.value
        assert isinstance(tag, AttributeType), 'attribute type error: %s' % tag
        assert isinstance(value, AttributeValue), 'attribute value error: %s' % value
        # check attributes
        if tag == MappedAddress:
            assert isinstance(value, MappedAddressValue), 'mapped address value error: %s' % value
            context['MAPPED-ADDRESS'] = value
        elif tag == XorMappedAddress:
            if not isinstance(value, XorMappedAddressValue):
                # XOR and parse again
                data = XorMappedAddressValue.xor(data=value, factor=context['trans_id'])
                length = AttributeLength(value=data.length)
                value = XorMappedAddressValue.parse(data=data, tag=tag, length=length)
            if value is not None:
                context['MAPPED-ADDRESS'] = value
        elif tag == XorMappedAddress2:
            if not isinstance(value, XorMappedAddressValue2):
                # XOR and parse again
                data = XorMappedAddressValue2.xor(data=value, factor=context['trans_id'])
                length = AttributeLength(value=data.length)
                value = XorMappedAddressValue2.parse(data=data, tag=tag, length=length)
            if value is not None:
                context['MAPPED-ADDRESS'] = value
        elif tag == ChangedAddress:
            assert isinstance(value, ChangedAddressValue), 'changed address value error: %s' % value
            context['CHANGED-ADDRESS'] = value
        elif tag == SourceAddress:
            assert isinstance(value, SourceAddressValue), 'source address value error: %s' % value
            context['SOURCE-ADDRESS'] = value
        elif tag == Software:
            assert isinstance(value, SoftwareValue), 'software value error: %s' % value
            context['SOFTWARE'] = value
        else:
            self.info('unknown attribute type: %s' % tag)
            return False
        self.info('%s:\t%s' % (tag, value))
        return True

    def __bind_request(self, remote_host: str, remote_port: int, body: Data) -> Optional[dict]:
        # 1. create STUN message package
        req = Package.new(msg_type=BindRequest, body=body)
        trans_id = req.head.trans_id
        # 2. send and get response
        count = 0
        while True:
            size = self.send(data=req, destination=(remote_host, remote_port))
            if size != req.length:
                # failed to send data
                return None
            cargo = self.receive()
            if cargo is None:
                if count < self.retries:
                    count += 1
                    self.info('(%d/%d) receive nothing' % (count, self.retries))
                else:
                    # failed to receive data
                    return None
            else:
                self.info('received %d bytes from %s' % (len(cargo.data), cargo.source))
                break
        # 3. parse response
        context = {
            'trans_id': trans_id,
        }
        data = Data(data=cargo.data)
        if not self.parse_data(data=data, context=context):
            return None
        head = context.get('head')
        if head is None or head.type != BindResponse or head.trans_id != trans_id:
            # received package error
            return None
        return context

    """
    [RFC] https://www.ietf.org/rfc/rfc3489.txt

    Rosenberg, et al.           Standards Track                    [Page 19]

    RFC 3489                          STUN                        March 2003


    The flow makes use of three tests.  In test I, the client sends a
    STUN Binding Request to a server, without any flags set in the
    CHANGE-REQUEST attribute, and without the RESPONSE-ADDRESS attribute.
    This causes the server to send the response back to the address and
    port that the request came from.  In test II, the client sends a
    Binding Request with both the "change IP" and "change port" flags
    from the CHANGE-REQUEST attribute set.  In test III, the client sends
    a Binding Request with only the "change port" flag set.
    """

    def __test_1(self, stun_host: str, stun_port: int) -> Optional[dict]:
        self.info('[Test 1] sending empty request ... (%s:%d)' % (stun_host, stun_port))
        body = Data.ZERO
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def __test_2(self, stun_host: str, stun_port: int) -> Optional[dict]:
        self.info('[Test 2] sending "ChangeIPAndPort" ... (%s:%d)' % (stun_host, stun_port))
        body = Attribute(tag=ChangeRequest, value=ChangeIPAndPort)
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def __test_3(self, stun_host: str, stun_port: int) -> Optional[dict]:
        self.info('[Test 3] sending "ChangePort" ... (%s:%d)' % (stun_host, stun_port))
        body = Attribute(tag=ChangeRequest, value=ChangePort)
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def get_nat_type(self, stun_host: str, stun_port: int = 3478) -> dict:
        # 1. Test I
        res1 = self.__test_1(stun_host=stun_host, stun_port=stun_port)
        if res1 is None:
            """
            The client begins by initiating test I.  If this test yields no
            response, the client knows right away that it is not capable of UDP
            connectivity.
            """
            res1 = {'NAT': NatType.UDPBlocked}
            return res1
        """
        If the test produces a response, the client examines the MAPPED-ADDRESS
        attribute.  If this address and port are the same as the local IP
        address and port of the socket used to send the request, the client
        knows that it is not NATed.  It executes test II.
        """
        ma1 = res1.get('MAPPED-ADDRESS')
        # 2. Test II
        res2 = self.__test_2(stun_host=stun_host, stun_port=stun_port)
        if ma1 is not None and (ma1.ip, ma1.port) == self.source_address:
            """
            If a response is received, the client knows that it has open access
            to the Internet (or, at least, its behind a firewall that behaves
            like a full-cone NAT, but without the translation).  If no response
            is received, the client knows its behind a symmetric UDP firewall.
            """
            if res2 is None:
                res1['NAT'] = NatType.SymmetricFirewall
                return res1
            else:
                res2['NAT'] = NatType.OpenInternet
                return res2
        elif res2 is not None:
            """
            In the event that the IP address and port of the socket did not match
            the MAPPED-ADDRESS attribute in the response to test I, the client
            knows that it is behind a NAT.  It performs test II.  If a response
            is received, the client knows that it is behind a full-cone NAT.
            """
            res2['NAT'] = NatType.FullConeNAT
            return res2
        """
        If no response is received, it performs test I again, but this time,
        does so to the address and port from the CHANGED-ADDRESS attribute
        from the response to test I.
        """
        ca1 = res1.get('CHANGED-ADDRESS')
        # 3. Test I'
        if ca1 is None:
            res1['NAT'] = 'Changed-Address not found'
            return res1
        assert isinstance(ca1, ChangedAddressValue), 'CHANGED-ADDRESS error: %s' % ca1
        changed_ip = ca1.ip
        changed_port = ca1.port
        res11 = self.__test_1(stun_host=changed_ip, stun_port=changed_port)
        if res11 is None:
            # raise AssertionError('network error')
            res1['NAT'] = 'Change address failed'
            return res1
        ma11 = res11.get('MAPPED-ADDRESS')
        if ma11 is None or ma1 is None or ma11.port != ma1.port or ma11.ip != ma1.ip:
            """
            If the IP address and port returned in the MAPPED-ADDRESS attribute
            are not the same as the ones from the first test I, the client
            knows its behind a symmetric NAT.
            """
            res11['NAT'] = NatType.SymmetricNAT
            return res11
        """
        If the address and port are the same, the client is either behind a
        restricted or port restricted NAT.  To make a determination about
        which one it is behind, the client initiates test III.  If a response
        is received, its behind a restricted NAT, and if no response is
        received, its behind a port restricted NAT.
        """
        # 4. Test III
        res3 = self.__test_3(stun_host=stun_host, stun_port=stun_port)
        if res3 is None:
            res11['NAT'] = NatType.PortRestrictedNAT
            return res11
        else:
            res3['NAT'] = NatType.RestrictedNAT
            return res3
