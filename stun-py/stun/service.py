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

"""

from abc import ABC, abstractmethod

from .protocol import *
from .attributes import *


class Result:
    """ Result info from response """

    UDPBlocked = 'UDP Blocked'
    OpenInternet = 'Open Internet'
    SymmetricFirewall = 'Symmetric UDP Firewall'
    SymmetricNAT = 'Symmetric NAT'
    FullConeNAT = 'Full Cone NAT'
    RestrictedNAT = 'Restricted Cone NAT'
    PortRestrictedNAT = 'Port Restricted Cone NAT'

    def __init__(self):
        # Bind Response
        self.external_ip = None
        self.external_port = 0
        self.changed_ip = None
        self.changed_port = 0
        self.source_ip = None
        self.source_port = 0


class Delegate(ABC):

    @abstractmethod
    def local_ip(self) -> str:
        raise NotImplemented

    @abstractmethod
    def local_port(self) -> int:
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, remote_host: str, remote_port: int) -> int:
        raise NotImplemented

    @abstractmethod
    def receive(self, buffer_size: int = 2048) -> (bytes, tuple):
        raise NotImplemented


class Server:

    def __init__(self):
        super().__init__()
        self.delegate = None


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


class Client:

    def __init__(self):
        super().__init__()
        self.delegate = None

    @staticmethod
    def _process(attribute: Attribute, trans_id: TransactionID, result: Result) -> Result:
        value = attribute.value
        # check attributes
        if attribute.type == MappedAddress:
            assert isinstance(value, MappedAddressValue), 'mapped address value error: %s' % value
            result.external_ip = value.ip
            result.external_port = value.port
        elif attribute.type == XorMappedAddress2:
            if not isinstance(value, XorMappedAddressValue2):
                # XOR and parse again
                data = XorMappedAddressValue2.xor(data=value.data, factor=trans_id.data)
                value = XorMappedAddressValue2.parse(data=data, length=len(data))
            result.external_ip = value.ip
            result.external_port = value.port
        elif attribute.type == XorMappedAddress:
            if not isinstance(value, XorMappedAddressValue):
                # XOR and parse again
                data = XorMappedAddressValue.xor(data=value.data, factor=trans_id.data)
                value = XorMappedAddressValue.parse(data=data, length=len(data))
            result.external_ip = value.ip
            result.external_port = value.port
        elif attribute.type == ChangedAddress:
            assert isinstance(value, ChangedAddressValue), 'changed address value error: %s' % value
            result.changed_ip = value.ip
            result.changed_port = value.port
        elif attribute.type == SourceAddress:
            assert isinstance(value, SourceAddressValue), 'source address value error: %s' % value
            result.source_ip = value.ip
            result.source_port = value.port
        elif attribute.type == Software:
            assert isinstance(value, SoftwareValue), 'software value error: %s' % value
        # else:
        #     print('unknown attribute type: %s' % attribute.type)
        return result

    def __bind_request(self, remote_host: str, remote_port: int, body: bytes) -> Optional[Result]:
        # 1. create STUN message package
        req = Package.new(msg_type=BindRequest, body=body)
        trans_id = req.head.trans_id
        # 2. send and get response
        count = 3
        res: bytes = None
        while res is None:
            size = self.delegate.send(data=req.data, remote_host=remote_host, remote_port=remote_port)
            if size != len(req.data):
                # failed to send data
                return None
            res, address = self.delegate.receive()
            if res is None:
                count -= 1
                if count <= 0:
                    # failed to receive data
                    return None
        # 3. parse response
        pack = Package.parse(data=res)
        if pack.head.type != BindResponse or pack.head.trans_id != trans_id:
            # received package error
            return None
        # 4. parse attributes
        ret = Result()
        attributes = Attribute.parse_all(data=pack.body)
        for item in attributes:
            ret = self._process(attribute=item, trans_id=trans_id, result=ret)
        return ret

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

    def __test_1(self, stun_host: str, stun_port: int) -> Optional[Result]:
        body = b''
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def __test_2(self, stun_host: str, stun_port: int) -> Optional[Result]:
        body = Attribute(ChangeRequest, ChangeIPAndPort).data
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def __test_3(self, stun_host: str, stun_port: int) -> Optional[Result]:
        body = Attribute(ChangeRequest, ChangePort).data
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def get_nat_type(self, stun_host: str, stun_port: int=3478) -> str:
        local_ip = self.delegate.local_ip()
        local_port = self.delegate.local_port()
        # 1. Test I
        res1 = self.__test_1(stun_host=stun_host, stun_port=stun_port)
        if res1 is None:
            """
            The client begins by initiating test I.  If this test yields no
            response, the client knows right away that it is not capable of UDP
            connectivity.
            """
            return Result.UDPBlocked
        same_address = (res1.external_ip == local_ip) and (res1.external_port == local_port)
        """
        If the test produces a response, the client examines the MAPPED-ADDRESS
        attribute.  If this address and port are the same as the local IP
        address and port of the socket used to send the request, the client
        knows that it is not NATed.  It executes test II.
        """
        # 2. Test II
        res2 = self.__test_2(stun_host=stun_host, stun_port=stun_port)
        if same_address:
            """
            If a response is received, the client knows that it has open access
            to the Internet (or, at least, its behind a firewall that behaves
            like a full-cone NAT, but without the translation).  If no response
            is received, the client knows its behind a symmetric UDP firewall.
            """
            if res2 is None:
                return Result.SymmetricFirewall
            else:
                return Result.OpenInternet
        if res2 is not None:
            """
            In the event that the IP address and port of the socket did not match
            the MAPPED-ADDRESS attribute in the response to test I, the client
            knows that it is behind a NAT.  It performs test II.  If a response
            is received, the client knows that it is behind a full-cone NAT.
            """
            return Result.FullConeNAT
        """
        If no response is received, it performs test I again, but this time,
        does so to the address and port from the CHANGED-ADDRESS attribute
        from the response to test I.
        """
        # 3. Test I'
        res11 = self.__test_1(stun_host=res1.changed_ip, stun_port=res1.changed_port)
        if res11 is None:
            raise AssertionError('network error')
        same_address = (res11.external_ip == local_ip and res11.external_port == local_port)
        if not same_address:
            """
            If the IP address and port returned in the MAPPED-ADDRESS attribute
            are not the same as the ones from the first test I, the client
            knows its behind a symmetric NAT.
            """
            return Result.SymmetricNAT
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
            return Result.PortRestrictedNAT
        else:
            return Result.RestrictedNAT
