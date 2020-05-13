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

    RFC - https://www.ietf.org/rfc/rfc5389.txt
"""

import socket

from .protocol import Package
from .protocol import BindRequest, BindResponse
from .protocol import Attribute, AttributeType
from .protocol import MappedAddressValue, XorMappedAddressValue


class UDPSocket:

    def __init__(self, local_host: str='0.0.0.0', local_port: int=9394):
        super().__init__()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(2)
        s.bind((local_host, local_port))
        self.__socket = s

    def send(self, data: bytes, remote_host: str, remote_port: int) -> int:
        try:
            return self.__socket.sendto(data, (remote_host, remote_port))
        except socket.error:
            return -1

    def receive(self, buffer_size: int=2048) -> (bytes, tuple):
        try:
            return self.__socket.recvfrom(buffer_size)
        except socket.error:
            return None, None

    # def send_receive(self, data: bytes, remote_host: str, remote_port: int) -> Optional[bytes]:
    #     size = self.send(data=data, remote_host=remote_host, remote_port=remote_port)
    #     if size != len(data):
    #         raise AssertionError('send failed: %d/%d', size, len(data))
    #     data, address = self.receive()
    #     # if address != (remote_host, remote_port):
    #     #     raise AssertionError('receive error: %s, %s' % (address, data))
    #     return data


class STUNSocket(UDPSocket):

    def __init__(self, local_host: str='0.0.0.0', local_port: int=9394):
        super().__init__(local_host=local_host, local_port=local_port)

    @staticmethod
    def _process_attribute(trans_id: bytes, attr_type: AttributeType, attr_value: bytes, result: dict):
        # check attributes
        if attr_type == AttributeType.MappedAddress:
            value = MappedAddressValue.parse(data=attr_value)
            result['ExternalIP'] = value.ip
            result['ExternalPort'] = value.port
        elif attr_type == AttributeType.XorMappedAddress:
            value = XorMappedAddressValue.xor(data=attr_value, factor=trans_id)
            value = MappedAddressValue.parse(data=value)
            result['ExternalIP'] = value.ip
            result['ExternalPort'] = value.port

    def __process(self, trans_id: bytes, body: bytes):
        result = {}
        remaining = len(body)
        while remaining > 0:
            attr = Attribute.parse(data=body)
            if attr is None:
                raise ValueError('attribute error: %s' % body)
            # cut this attribute
            a_len = 4 + attr.length
            remaining -= a_len
            body = body[a_len:]
            self._process_attribute(trans_id=trans_id, attr_type=attr.type, attr_value=attr.value, result=result)
        # BindResponse OK
        return result

    def __bind_request(self, remote_host: str, remote_port: int=3478, data: bytes=b''):
        # create STUN message package
        request = Package.new(msg_type=BindRequest, body=data)
        pack = None
        # send and get response
        count = 3
        while pack is None:
            size = self.send(data=request.data, remote_host=remote_host, remote_port=remote_port)
            if size != len(data):
                # failed to send data
                return None
            pack, address = self.receive()
            if pack is None:
                if --count < 0:
                    # failed to receive data
                    return None
        assert isinstance(pack, bytes), 'response error: %s' % pack
        response = Package.parse(data=pack)
        if response.head.type != BindResponse or response.head.id != request.head.id:
            # received package error
            return None
        return self.__process(trans_id=response.head.id, body=response.body)

    def get_nat_type(self, stun_host: str, stun_port: int=3478):
        result = self.__bind_request(remote_host=stun_host, remote_port=stun_port)
        if result is None:
            return 'Blocked', result
