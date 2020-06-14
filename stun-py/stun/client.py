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

    Client node
"""

from abc import ABC
from typing import Optional

from .protocol import Package
from .protocol import BindRequest, BindResponse
from .attributes import Attribute, AttributeLength
from .attributes import ChangePort, ChangeIPAndPort
from .attributes import ChangeRequest
from .attributes import MappedAddress, MappedAddressValue
from .attributes import XorMappedAddress, XorMappedAddressValue
from .attributes import XorMappedAddress2, XorMappedAddressValue2
from .attributes import SourceAddress, SourceAddressValue
from .attributes import ChangedAddress, ChangedAddressValue
from .attributes import Software, SoftwareValue
from .node import Node, Info


class NatType:
    UDPBlocked = 'UDP Blocked'
    OpenInternet = 'Open Internet'
    SymmetricFirewall = 'Symmetric UDP Firewall'
    SymmetricNAT = 'Symmetric NAT'
    FullConeNAT = 'Full Cone NAT'
    RestrictedNAT = 'Restricted Cone NAT'
    PortRestrictedNAT = 'Port Restricted Cone NAT'


"""
[RFC] https://www.ietf.org/rfc/rfc3489.txt

Rosenberg, et al.           Standards Track                    [Page 21]

RFC 3489                          STUN                        March 2003


                        +--------+
                        |  Test  |
                        |   I    |
                        +--------+
                             |
                             |
                             V
                            /\              /\
                         N /  \ Y          /  \ Y             +--------+
          UDP     <-------/Resp\--------->/ IP \------------->|  Test  |
          Blocked         \ ?  /          \Same/              |   II   |
                           \  /            \? /               +--------+
                            \/              \/                    |
                                             | N                  |
                                             |                    V
                                             V                    /\
                                         +--------+  Sym.      N /  \
                                         |  Test  |  UDP    <---/Resp\
                                         |   II   |  Firewall   \ ?  /
                                         +--------+              \  /
                                             |                    \/
                                             V                     |Y
                  /\                         /\                    |
   Symmetric  N  /  \       +--------+   N  /  \                   V
      NAT  <--- / IP \<-----|  Test  |<--- /Resp\               Open
                \Same/      |   I    |     \ ?  /               Internet
                 \? /       +--------+      \  /
                  \/                         \/
                  |                           |Y
                  |                           |
                  |                           V
                  |                           Full
                  |                           Cone
                  V              /\
              +--------+        /  \ Y
              |  Test  |------>/Resp\---->Restricted
              |   III  |       \ ?  /
              +--------+        \  /
                                 \/
                                  |N
                                  |       Port
                                  +------>Restricted

                 Figure 2: Flow for type discovery process
"""


class Client(Node, ABC):

    def __init__(self):
        super().__init__()
        self.retries = 3

    def parse_attribute(self, attribute: Attribute, context: dict, result: Info) -> Info:
        a_type = attribute.type
        a_value = attribute.value
        # check attributes
        if a_type == MappedAddress:
            assert isinstance(a_value, MappedAddressValue), 'mapped address value error: %s' % a_value
            result.mapped_address = (a_value.ip, a_value.port)
            self.info('MappedAddress:\t(%s:%d)' % (a_value.ip, a_value.port))
        elif a_type == XorMappedAddress:
            if not isinstance(a_value, XorMappedAddressValue):
                # XOR and parse again
                data = XorMappedAddressValue.xor(data=a_value.data, factor=context['trans_id'])
                a_len = AttributeLength(len(data))
                a_value = XorMappedAddressValue.parse(data=data, t=a_type, length=a_len)
            result.mapped_address = (a_value.ip, a_value.port)
            self.info('XorMappedAddress:\t(%s:%d)' % (a_value.ip, a_value.port))
        elif a_type == XorMappedAddress2:
            if not isinstance(a_value, XorMappedAddressValue2):
                # XOR and parse again
                data = XorMappedAddressValue2.xor(data=a_value.data, factor=context['trans_id'])
                a_len = AttributeLength(len(data))
                a_value = XorMappedAddressValue2.parse(data=data, t=a_type, length=a_len)
            result.mapped_address = (a_value.ip, a_value.port)
            self.info('XorMappedAddress2:\t(%s:%d)' % (a_value.ip, a_value.port))
        elif a_type == ChangedAddress:
            assert isinstance(a_value, ChangedAddressValue), 'changed address value error: %s' % a_value
            result.changed_address = (a_value.ip, a_value.port)
            self.info('ChangedAddress:\t(%s:%d)' % (a_value.ip, a_value.port))
        elif a_type == SourceAddress:
            assert isinstance(a_value, SourceAddressValue), 'source address value error: %s' % a_value
            result.source_address = (a_value.ip, a_value.port)
            self.info('SourceAddress:\t(%s:%d)' % (a_value.ip, a_value.port))
        elif a_type == Software:
            assert isinstance(a_value, SoftwareValue), 'software value error: %s' % a_value
            self.info(('Software: %s' % a_value.description))
        else:
            self.info('unknown attribute type: %s' % a_type)
        return result

    def __bind_request(self, remote_host: str, remote_port: int, body: bytes) -> Optional[Info]:
        # 1. create STUN message package
        req = Package.new(msg_type=BindRequest, body=body)
        trans_id = req.head.trans_id
        # 2. send and get response
        count = 0
        while True:
            size = self.send(data=req.data, destination=(remote_host, remote_port))
            if size != len(req.data):
                # failed to send data
                return None
            res, address = self.receive()
            if res is None:
                if count < self.retries:
                    count += 1
                    self.info('(%d/%d) receive nothing from %s' % (count, self.retries, address))
                else:
                    # failed to receive data
                    return None
            else:
                self.info('received %d bytes from %s' % (len(res), address))
                break
        # 3. parse response
        context = {
            'trans_id': trans_id.data,
        }
        head, result = self.parse_data(data=res, context=context)
        if head is None or head.type != BindResponse or head.trans_id != trans_id:
            # received package error
            return None
        return result

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

    def __test_1(self, stun_host: str, stun_port: int) -> Optional[Info]:
        self.info('[Test 1] sending empty request ... (%s:%d)' % (stun_host, stun_port))
        body = b''
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def __test_2(self, stun_host: str, stun_port: int) -> Optional[Info]:
        self.info('[Test 2] sending "ChangeIPAndPort" ... (%s:%d)' % (stun_host, stun_port))
        body = Attribute(ChangeRequest, ChangeIPAndPort).data
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def __test_3(self, stun_host: str, stun_port: int) -> Optional[Info]:
        self.info('[Test 3] sending "ChangePort" ... (%s:%d)' % (stun_host, stun_port))
        body = Attribute(ChangeRequest, ChangePort).data
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def get_nat_type(self, stun_host: str, stun_port: int = 3478) -> (str, Optional[Info]):
        # 1. Test I
        res1 = self.__test_1(stun_host=stun_host, stun_port=stun_port)
        if res1 is None:
            """
            The client begins by initiating test I.  If this test yields no
            response, the client knows right away that it is not capable of UDP
            connectivity.
            """
            return NatType.UDPBlocked, None
        """
        If the test produces a response, the client examines the MAPPED-ADDRESS
        attribute.  If this address and port are the same as the local IP
        address and port of the socket used to send the request, the client
        knows that it is not NATed.  It executes test II.
        """
        # 2. Test II
        res2 = self.__test_2(stun_host=stun_host, stun_port=stun_port)
        if res1.mapped_address == self.source_address:
            """
            If a response is received, the client knows that it has open access
            to the Internet (or, at least, its behind a firewall that behaves
            like a full-cone NAT, but without the translation).  If no response
            is received, the client knows its behind a symmetric UDP firewall.
            """
            if res2 is None:
                return NatType.SymmetricFirewall, res1
            else:
                return NatType.OpenInternet, res2
        elif res2 is not None:
            """
            In the event that the IP address and port of the socket did not match
            the MAPPED-ADDRESS attribute in the response to test I, the client
            knows that it is behind a NAT.  It performs test II.  If a response
            is received, the client knows that it is behind a full-cone NAT.
            """
            return NatType.FullConeNAT, res2
        """
        If no response is received, it performs test I again, but this time,
        does so to the address and port from the CHANGED-ADDRESS attribute
        from the response to test I.
        """
        # 3. Test I'
        if res1.changed_address is None:
            return 'Change-Address not found', res1
        changed_ip = res1.changed_address[0]
        changed_port = res1.changed_address[1]
        res11 = self.__test_1(stun_host=changed_ip, stun_port=changed_port)
        if res11 is None:
            # raise AssertionError('network error')
            return 'Change address failed', res1
        if res11.mapped_address != res1.mapped_address:
            """
            If the IP address and port returned in the MAPPED-ADDRESS attribute
            are not the same as the ones from the first test I, the client
            knows its behind a symmetric NAT.
            """
            return NatType.SymmetricNAT, res11
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
            return NatType.PortRestrictedNAT, res11
        else:
            return NatType.RestrictedNAT, res3
