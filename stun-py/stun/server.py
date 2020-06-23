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

    Server node
"""

from abc import ABC

from .protocol import Package, Header
from .protocol import BindRequest, BindResponse
from .attributes import Attribute
from .attributes import ChangePort, ChangeIPAndPort
from .attributes import ChangeRequest, ChangeRequestValue
from .attributes import MappedAddress, MappedAddressValue
from .attributes import XorMappedAddress, XorMappedAddressValue
from .attributes import XorMappedAddress2, XorMappedAddressValue2
from .attributes import SourceAddress, SourceAddressValue
from .attributes import ChangedAddress, ChangedAddressValue
from .attributes import Software, SoftwareValue
from .node import Node, Info


class Server(Node, ABC):

    def __init__(self, host: str='0.0.0.0', port: int=3478, change_port: int=3479):
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
        assert change_port > 0, 'change port error'
        self.hub.open(host=host, port=change_port)

    def parse_attribute(self, attribute: Attribute, context: dict, result: Info) -> Info:
        value = attribute.value
        # check attributes
        if attribute.tag == MappedAddress:
            assert isinstance(value, MappedAddressValue), 'mapped address value error: %s' % value
            result.mapped_address = (value.ip, value.port)
            self.info('MappedAddress:\t(%s:%d)' % (value.ip, value.port))
        elif attribute.tag == ChangeRequest:
            assert isinstance(value, ChangeRequestValue), 'change request value error: %s' % value
            result.change_request = value
            self.info('ChangeRequest: %s' % value)
        else:
            self.info('unknown attribute type: %s' % attribute.tag)
        return result

    def _redirect(self, head: Header, remote_ip: str, remote_port: int):
        """
        Redirect the request to the neighbor server

        :param remote_ip:   Client's mapped IP address
        :param remote_port: Client's mapped address port
        :return:
        """
        assert self.neighbour is not None, 'neighbour address not set'
        # create attributes
        value = MappedAddressValue.new(ip=remote_ip, port=remote_port)
        data1 = Attribute(MappedAddress, value).data
        # pack
        body = data1
        pack = Package.new(msg_type=head.type, trans_id=head.trans_id, body=body)
        self.send(data=pack.data, destination=self.neighbour)

    def _respond(self, head: Header, remote_ip: str, remote_port: int, local_port: int = 0):
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
            self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port, local_port=self.change_port)
        elif result.mapped_address is None:
            # respond origin request
            self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port)
        else:
            # respond redirected request
            remote_ip = result.mapped_address[0]
            remote_port = result.mapped_address[1]
            self._respond(head=head, remote_ip=remote_ip, remote_port=remote_port, local_port=self.change_port)
