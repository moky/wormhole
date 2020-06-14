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

    Common interfaces for STUN Server or Client nodes
"""

import socket
import time
from abc import ABC, abstractmethod
from typing import Union, Optional

from .protocol import Package, Header
from .attributes import Attribute, ChangeRequestValue


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

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
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


def get_local_ip(remote_host: str = '8.8.8.8', remote_port: int = 80) -> Optional[str]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((remote_host, remote_port))
        ip = sock.getsockname()[0]
    finally:
        # noinspection PyUnboundLocalVariable
        sock.close()
    return ip
