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

import time
from abc import ABC, abstractmethod

from .protocol import *
from .attributes import *


class Info(dict):
    """
        1. Parameters from request
        2. Result info from response
    """

    UDPBlocked = 'UDP Blocked'
    OpenInternet = 'Open Internet'
    SymmetricFirewall = 'Symmetric UDP Firewall'
    SymmetricNAT = 'Symmetric NAT'
    FullConeNAT = 'Full Cone NAT'
    RestrictedNAT = 'Restricted Cone NAT'
    PortRestrictedNAT = 'Port Restricted Cone NAT'

    def __init__(self):
        super().__init__()
        # Bind Request
        self.change_request: ChangeRequestValue = None
        # Bind Response
        self.mapped_address: tuple = None
        self.changed_address: tuple = None
        self.source_address: tuple = None


class Node(ABC):

    def __init__(self):
        super().__init__()
        """
        11.2.5 SOURCE-ADDRESS

            The SOURCE-ADDRESS attribute is present in Binding Responses.  It
            indicates the source IP address and port that the server is sending
            the response from.  Its syntax is identical to that of MAPPED-
            ADDRESS.
            
            
            Whether it's a server or a client, this indicates the current node's
            local address: (ip, port)
        """
        self.source_address: tuple = None

    @staticmethod
    def info(msg: str):
        time_array = time.localtime(int(time.time()))
        time_string = time.strftime('%y-%m-%d %H:%M:%S', time_array)
        print('[%s] %s' % (time_string, msg))

    @abstractmethod
    def send(self, data: bytes, remote_host: str, remote_port: int) -> int:
        raise NotImplemented

    @abstractmethod
    def receive(self, buffer_size: int = 2048) -> (bytes, tuple):
        raise NotImplemented

    @abstractmethod
    def parse_attribute(self, attribute: Attribute, context: dict, result: Info) -> Info:
        raise NotImplemented

    def parse_data(self, data: bytes, context: dict) -> tuple:
        # 1. parse STUN package
        pack = Package.parse(data=data)
        if pack is None:
            self.info('failed to parse package data: %d' % len(data))
            return None, None
        # 2. parse attributes
        result = Info()
        attributes = Attribute.parse_all(data=pack.body)
        for item in attributes:
            # 3. process attribute
            result = self.parse_attribute(attribute=item, context=context, result=result)
        return pack.head, result


class Server(Node, ABC):

    def __init__(self):
        super().__init__()
        self.software = 'stun.dim.chat 0.1'
        """
        11.2.3  CHANGED-ADDRESS

            The CHANGED-ADDRESS attribute indicates the IP address and port where
            responses would have been sent from if the "change IP" and "change
            port" flags had been set in the CHANGE-REQUEST attribute of the
            Binding Request.  The attribute is always present in a Binding
            Response, independent of the value of the flags.  Its syntax is
            identical to MAPPED-ADDRESS.
        """
        self.changed_address: tuple = None
        """
            "Change IP and Port"
            
            When this server A received ChangeRequest with "change IP" and
            "change port" flags set, it should redirect this request to the
            neighbour server B to (use another address) respond the client.
            
            This address will be the same as CHANGED-ADDRESS by default, but
            offer another different IP address here will be better.
        """
        self.neighbour_address: tuple = None
        """
            "Change Port"
            
            When this server received ChangeRequest with "change port" flag set,
            it should respond the client with another port.
        """
        self.another_port: int = 3479

    @abstractmethod
    def send(self, data: bytes, remote_host: str, remote_port: int, local_port: int=0) -> int:
        raise NotImplemented

    def parse_attribute(self, attribute: Attribute, context: dict, result: Info) -> Info:
        value = attribute.value
        # check attributes
        if attribute.type == MappedAddress:
            assert isinstance(value, MappedAddressValue), 'mapped address value error: %s' % value
            result.mapped_address = (value.ip, value.port)
            self.info('MappedAddress:\t(%s:%d)' % (value.ip, value.port))
        elif attribute.type == ChangeRequest:
            assert isinstance(value, ChangeRequestValue), 'change request value error: %s' % value
            result.change_request = value
            self.info('ChangeRequest: %s' % value)
        else:
            self.info('unknown attribute type: %s' % attribute.type)
        return result

    def _redirect(self, head: Header, remote_ip: str, remote_port: int):
        """
        Redirect the request to the neighbor server

        :param remote_ip:   Client's mapped IP address
        :param remote_port: Client's mapped address port
        :return:
        """
        if self.neighbour_address is None:
            neighbour_ip = self.changed_address[0]
            neighbour_port = self.changed_address[1]
        else:
            neighbour_ip = self.neighbour_address[0]
            neighbour_port = self.neighbour_address[1]
        # create attributes
        value = MappedAddressValue.new(ip=remote_ip, port=remote_port)
        data1 = Attribute(MappedAddress, value).data
        # pack
        body = data1
        pack = Package.new(msg_type=head.type, trans_id=head.trans_id, body=body)
        self.send(data=pack.data, remote_host=neighbour_ip, remote_port=neighbour_port)

    def _respond(self, head: Header, remote_ip: str, remote_port: int, local_port: int=0):
        local_ip = self.source_address[0]
        if local_port is 0:
            local_port = self.source_address[1]
        if self.changed_address is None:
            changed_ip = self.neighbour_address[0]
            changed_port = self.neighbour_address[1]
        else:
            changed_ip = self.changed_address[0]
            changed_port = self.changed_address[1]
        # create attributes
        value = MappedAddressValue.new(ip=remote_ip, port=remote_port)
        data1 = Attribute(MappedAddress, value).data
        # Xor
        value = XorMappedAddressValue.new(ip=remote_ip, port=remote_port, factor=head.trans_id.data)
        data4 = Attribute(XorMappedAddress, value).data
        # Xor2
        value = XorMappedAddressValue2.new(ip=remote_ip, port=remote_port, factor=head.trans_id.data)
        data5 = Attribute(XorMappedAddress2, value).data
        # source address
        value = SourceAddressValue.new(ip=local_ip, port=local_port)
        data2 = Attribute(SourceAddress, value).data
        # changed address
        value = ChangedAddressValue.new(ip=changed_ip, port=changed_port)
        data3 = Attribute(ChangedAddress, value).data
        # software
        value = SoftwareValue.new(description=self.software)
        data6 = Attribute(Software, value).data
        # pack
        body = data1 + data2 + data3 + data4 + data5 + data6
        pack = Package.new(msg_type=BindResponse, trans_id=head.trans_id, body=body)
        self.send(data=pack.data, remote_host=remote_ip, remote_port=remote_port, local_port=local_port)

    def handle(self, data: bytes, remote_ip: str, remote_port: int):
        # 1. parse request
        context = {
            remote_ip: remote_ip,
            remote_port: remote_port,
        }
        head, result = self.parse_data(data=data, context=context)
        if head is None or head.type != BindRequest:
            # received package error
            return None
        self.info('received message type: %s' % head.type)
        if result.change_request == ChangeIPAndPort:
            # redirect for "change IP" and "change port" flags
            self._redirect(head=head, remote_ip=remote_ip, remote_port=remote_port)
        elif result.change_request == ChangePort:
            # respond with another port for "change port" flag
            self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port, local_port=self.another_port)
        elif result.mapped_address is None:
            # respond origin request
            self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port)
        else:
            # respond redirected request
            remote_ip = result.mapped_address[0]
            remote_port = result.mapped_address[1]
            self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port)


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
        value = attribute.value
        # check attributes
        if attribute.type == MappedAddress:
            assert isinstance(value, MappedAddressValue), 'mapped address value error: %s' % value
            result.mapped_address = (value.ip, value.port)
            self.info('MappedAddress:\t(%s:%d)' % (value.ip, value.port))
        elif attribute.type == XorMappedAddress:
            if not isinstance(value, XorMappedAddressValue):
                # XOR and parse again
                data = XorMappedAddressValue.xor(data=value.data, factor=context['trans_id'])
                value = XorMappedAddressValue.parse(data=data, length=len(data))
            result.mapped_address = (value.ip, value.port)
            self.info('XorMappedAddress:\t(%s:%d)' % (value.ip, value.port))
        elif attribute.type == XorMappedAddress2:
            if not isinstance(value, XorMappedAddressValue2):
                # XOR and parse again
                data = XorMappedAddressValue2.xor(data=value.data, factor=context['trans_id'])
                value = XorMappedAddressValue2.parse(data=data, length=len(data))
            result.mapped_address = (value.ip, value.port)
            self.info('XorMappedAddress2:\t(%s:%d)' % (value.ip, value.port))
        elif attribute.type == ChangedAddress:
            assert isinstance(value, ChangedAddressValue), 'changed address value error: %s' % value
            result.changed_address = (value.ip, value.port)
            self.info('ChangedAddress:\t(%s:%d)' % (value.ip, value.port))
        elif attribute.type == SourceAddress:
            assert isinstance(value, SourceAddressValue), 'source address value error: %s' % value
            result.source_address = (value.ip, value.port)
            self.info('SourceAddress:\t(%s:%d)' % (value.ip, value.port))
        elif attribute.type == Software:
            assert isinstance(value, SoftwareValue), 'software value error: %s' % value
            self.info(('Software: %s' % value.description))
        else:
            self.info('unknown attribute type: %s' % attribute.type)
        return result

    def __bind_request(self, remote_host: str, remote_port: int, body: bytes) -> Optional[Info]:
        # 1. create STUN message package
        req = Package.new(msg_type=BindRequest, body=body)
        trans_id = req.head.trans_id
        # 2. send and get response
        count = 0
        while True:
            size = self.send(data=req.data, remote_host=remote_host, remote_port=remote_port)
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
        self.info('[Test 2] sending "ChangeIPAmdPort" ... (%s:%d)' % (stun_host, stun_port))
        body = Attribute(ChangeRequest, ChangeIPAndPort).data
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def __test_3(self, stun_host: str, stun_port: int) -> Optional[Info]:
        self.info('[Test 3] sending "ChangePort" ... (%s:%d)' % (stun_host, stun_port))
        body = Attribute(ChangeRequest, ChangePort).data
        return self.__bind_request(remote_host=stun_host, remote_port=stun_port, body=body)

    def get_nat_type(self, stun_host: str, stun_port: int=3478) -> str:
        # 1. Test I
        res1 = self.__test_1(stun_host=stun_host, stun_port=stun_port)
        if res1 is None:
            """
            The client begins by initiating test I.  If this test yields no
            response, the client knows right away that it is not capable of UDP
            connectivity.
            """
            return Info.UDPBlocked
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
                return Info.SymmetricFirewall
            else:
                return Info.OpenInternet
        if res2 is not None:
            """
            In the event that the IP address and port of the socket did not match
            the MAPPED-ADDRESS attribute in the response to test I, the client
            knows that it is behind a NAT.  It performs test II.  If a response
            is received, the client knows that it is behind a full-cone NAT.
            """
            return Info.FullConeNAT
        """
        If no response is received, it performs test I again, but this time,
        does so to the address and port from the CHANGED-ADDRESS attribute
        from the response to test I.
        """
        # 3. Test I'
        if res1.changed_address is None:
            return 'Change-Address not found'
        changed_ip = res1.changed_address[0]
        changed_port = res1.changed_address[1]
        res11 = self.__test_1(stun_host=changed_ip, stun_port=changed_port)
        if res11 is None:
            # raise AssertionError('network error')
            return 'Change-Address error on (%s:%d)' % (changed_ip, changed_port)
        if res11.mapped_address != res1.mapped_address:
            """
            If the IP address and port returned in the MAPPED-ADDRESS attribute
            are not the same as the ones from the first test I, the client
            knows its behind a symmetric NAT.
            """
            return Info.SymmetricNAT
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
            return Info.PortRestrictedNAT
        else:
            return Info.RestrictedNAT
