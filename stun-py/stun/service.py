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

import socket
import time
from abc import ABC, abstractmethod
from typing import Union

from .protocol import *
from .attributes import *


class NatType:

    UDPBlocked = 'UDP Blocked'
    OpenInternet = 'Open Internet'
    SymmetricFirewall = 'Symmetric UDP Firewall'
    SymmetricNAT = 'Symmetric NAT'
    FullConeNAT = 'Full Cone NAT'
    RestrictedNAT = 'Restricted Cone NAT'
    PortRestrictedNAT = 'Port Restricted Cone NAT'


class Info(dict):
    """
        1. Parameters from request
        2. Result info from response
    """

    def __init__(self):
        super().__init__()
        # Bind Request
        self.change_request: ChangeRequestValue = None
        # Bind Response
        self.mapped_address: (str, int) = None
        self.changed_address: (str, int) = None
        self.source_address: (str, int) = None


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
        self.source_address: (str, int) = None

    @staticmethod
    def info(msg: str):
        time_array = time.localtime(int(time.time()))
        time_string = time.strftime('%y-%m-%d %H:%M:%S', time_array)
        print('[%s] %s' % (time_string, msg))

    @abstractmethod
    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        """
        Send data to remote address

        :param data:
        :param destination: remote address
        :param source:      local address
        :return: count of sent bytes
        """
        raise NotImplemented

    @abstractmethod
    def receive(self) -> (bytes, (str, int)):
        """
        Received data from local port

        :return: data and remote address
        """
        raise NotImplemented

    @abstractmethod
    def parse_attribute(self, attribute: Attribute, context: dict, result: Info) -> Info:
        """
        Parse attribute

        :param attribute:
        :param context:
        :param result:
        :return:
        """
        raise NotImplemented

    def parse_data(self, data: bytes, context: dict) -> (Optional[Header], Optional[Info]):
        """
        Parse package data

        :param data:
        :param context:
        :return: package head and results from body
        """
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
        self.changed_address: (str, int) = None
        """
            "Change IP and Port"
            
            When this server A received ChangeRequest with "change IP" and
            "change port" flags set, it should redirect this request to the
            neighbour server B to (use another address) respond the client.
            
            This address will be the same as CHANGED-ADDRESS by default, but
            offer another different IP address here will be better.
        """
        self.neighbour_address: (str, int) = None
        """
            If the request is redirected by another server ("change IP" and
            "change port"), then use this port to respond the client.
        """
        self.redirected_port: int = 3480
        """
            "Change Port"
            
            When this server received ChangeRequest with "change port" flag set,
            it should respond the client with another port.
        """
        self.another_port: int = 3479

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
        assert self.neighbour_address is not None, 'neighbour address not set'
        # create attributes
        value = MappedAddressValue.new(ip=remote_ip, port=remote_port)
        data1 = Attribute(MappedAddress, value).data
        # pack
        body = data1
        pack = Package.new(msg_type=head.type, trans_id=head.trans_id, body=body)
        self.send(data=pack.data, destination=self.neighbour_address)

    def _respond(self, head: Header, remote_ip: str, remote_port: int, local_port: int=0):
        assert self.source_address is not None, 'source address not set'
        local_ip = self.source_address[0]
        if local_port is 0:
            local_port = self.source_address[1]
        assert self.changed_address is not None, 'changed address not set'
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
        self.send(data=pack.data, destination=(remote_ip, remote_port), source=(local_ip, local_port))

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
            self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port, local_port=self.redirected_port)


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

    def get_nat_type(self, stun_host: str, stun_port: int=3478) -> (str, Optional[Info]):
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

    @classmethod
    def get_local_ip(cls, remote_host: str='8.8.8.8', remote_port: int=80) -> Optional[str]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((remote_host, remote_port))
            return sock.getsockname()[0]
        finally:
            # noinspection PyUnboundLocalVariable
            sock.close()
