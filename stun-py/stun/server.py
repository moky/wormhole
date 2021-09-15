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

    Server node
"""

from abc import ABC

from udp.ba import MutableData

from .protocol import Package, Header, MessageType
from .protocol import Attribute, AttributeType
from .protocol import MappedAddressValue, XorMappedAddressValue, XorMappedAddressValue2
from .protocol import SourceAddressValue, ChangedAddressValue
from .protocol import ChangeRequestValue, SoftwareValue
from .node import Node


class Server(Node, ABC):

    def __init__(self, host: str = '0.0.0.0', port: int = 3478, change_port: int = 3479):
        super().__init__(host=host, port=port)
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
        self.neighbour: (str, int) = None
        """
            "Change Port"

            When this server received ChangeRequest with "change port" flag set,
            it should respond the client with another port.
        """
        self.change_port: int = change_port

    # Override
    def parse_attribute(self, attribute: Attribute, context: dict) -> bool:
        tag = attribute.tag
        value = attribute.value
        # check attributes
        if tag == AttributeType.MAPPED_ADDRESS:
            assert isinstance(value, MappedAddressValue), 'mapped address value error: %s' % value
            context['MAPPED-ADDRESS'] = value
        elif tag == AttributeType.CHANGE_REQUEST:
            assert isinstance(value, ChangeRequestValue), 'change request value error: %s' % value
            context['CHANGE-REQUEST'] = value
        else:
            self.info('unknown attribute type: %s' % tag)
            return False
        self.info('%s: %s' % (tag, value))
        return True

    def _redirect(self, head: Header, remote_ip: str, remote_port: int) -> bool:
        """
        Redirect the request to the neighbor server

        :param remote_ip:   Client's mapped IP address
        :param remote_port: Client's mapped address port
        :return:
        """
        assert self.neighbour is not None, 'neighbour address not set'
        # create attributes
        value = MappedAddressValue.new_ipv4(ip=remote_ip, port=remote_port)
        data1 = Attribute.new(tag=AttributeType.MAPPED_ADDRESS, value=value)
        # pack
        body = data1
        pack = Package.new(msg_type=head.msg_type, trans_id=head.trans_id, body=body)
        return self.send(data=pack.get_bytes(), destination=self.neighbour)

    def _respond(self, head: Header, remote_ip: str, remote_port: int, local_port: int) -> bool:
        # local (server) address
        assert self.source_address is not None, 'source address not set'
        local_ip = self.source_address[0]
        assert local_port > 0, 'local port error'
        # changed (another) address
        assert self.changed_address is not None, 'changed address not set'
        changed_ip = self.changed_address[0]
        changed_port = self.changed_address[1]
        # create attributes
        value = MappedAddressValue.new_ipv4(ip=remote_ip, port=remote_port)
        data1 = Attribute.new(tag=AttributeType.MAPPED_ADDRESS, value=value)
        # Xor
        data = XorMappedAddressValue.xor(data=value, factor=head.trans_id)
        value = XorMappedAddressValue(data=data, ip=remote_ip, port=remote_port, family=value.family)
        data4 = Attribute.new(tag=AttributeType.XOR_MAPPED_ADDRESS, value=value)
        # Xor2
        data = XorMappedAddressValue2.xor(data=value, factor=head.trans_id)
        value = XorMappedAddressValue2(data=data, ip=remote_ip, port=remote_port, family=value.family)
        data5 = Attribute.new(tag=AttributeType.XOR_MAPPED_ADDRESS2, value=value)
        # source address
        value = SourceAddressValue.new_ipv4(ip=local_ip, port=local_port)
        data2 = Attribute.new(tag=AttributeType.SOURCE_ADDRESS, value=value)
        # changed address
        value = ChangedAddressValue.new_ipv4(ip=changed_ip, port=changed_port)
        data3 = Attribute.new(tag=AttributeType.CHANGED_ADDRESS, value=value)
        # software
        value = SoftwareValue.new(description=self.software)
        data6 = Attribute.new(tag=AttributeType.SOFTWARE, value=value)
        # pack
        length = data1.size + data2.size + data3.size + data4.size + data5.size + data6.size
        body = MutableData(capacity=length)
        body.append(data1)
        body.append(data2)
        body.append(data3)
        body.append(data4)
        body.append(data5)
        body.append(data6)
        pack = Package.new(msg_type=MessageType.BIND_RESPONSE, trans_id=head.trans_id, body=body)
        return self.send(data=pack.get_bytes(), destination=(remote_ip, remote_port), source=(local_ip, local_port))

    def handle(self, data: bytes, remote_ip: str, remote_port: int) -> bool:
        # parse request
        context = {}
        ok = self.parse_data(data=data, context=context)
        head = context.get('head')
        if not ok or head is None or head.msg_type != MessageType.BIND_REQUEST:
            # received package error
            return False
        self.info('received message type: %s' % head.msg_type)
        change_request = context.get('CHANGE-REQUEST')
        if change_request == ChangeRequestValue.CHANGE_IP_AND_PORT:
            # redirect for "change IP" and "change port" flags
            return self._redirect(head=head, remote_ip=remote_ip, remote_port=remote_port)
        elif change_request == ChangeRequestValue.CHANGE_PORT:
            # respond with another port for "change port" flag
            return self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port, local_port=self.change_port)
        mapped_address = context.get('MAPPED-ADDRESS')
        if mapped_address is None:
            # respond origin request
            local_port = self.source_address[1]
            return self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port, local_port=local_port)
        else:
            assert isinstance(mapped_address, MappedAddressValue), 'MAPPED-ADDRESS error: %s' % mapped_address
            # respond redirected request
            remote_ip = mapped_address.ip
            remote_port = mapped_address.port
            return self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port, local_port=self.change_port)
