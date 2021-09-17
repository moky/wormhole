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

    Common interfaces for STUN Server or Client nodes
"""

from abc import ABC, abstractmethod
from typing import Union

from .protocol import Package, Attribute


"""
    [RFC] https://www.ietf.org/rfc/rfc3489.txt

    Rosenberg, et al.           Standards Track                    [Page 21]

    RFC 3489                          STUN                        March 2003

                 Figure 2: Flow for type discovery process
"""


class NatType:
    UDPBlocked = 'UDP Blocked'
    OpenInternet = 'Open Internet'
    SymmetricFirewall = 'Symmetric UDP Firewall'
    SymmetricNAT = 'Symmetric NAT'
    FullConeNAT = 'Full Cone NAT'
    RestrictedNAT = 'Restricted Cone NAT'
    PortRestrictedNAT = 'Port Restricted Cone NAT'


class Node(ABC):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)

    @property
    def source_address(self) -> tuple:
        """
        11.2.5 SOURCE-ADDRESS

            The SOURCE-ADDRESS attribute is present in Binding Responses.  It
            indicates the source IP address and port that the server is sending
            the response from.  Its syntax is identical to that of MAPPED-
            ADDRESS.


            Whether it's a server or a client, this indicates the current node's
            local address: (ip, port)
        """
        return self.__local_address

    def info(self, msg: str):
        # override to print logs
        pass

    @abstractmethod
    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> bool:
        """
        Send data to remote address

        :param data:
        :param destination: remote address
        :param source:      local address
        :return: False on failed
        """
        raise NotImplemented

    @abstractmethod
    def parse_attribute(self, attribute: Attribute, context: dict) -> bool:
        """
        Parse attribute

        :param attribute:
        :param context:
        :return: False on failed
        """
        raise NotImplemented

    def parse_data(self, data: bytes, context: dict) -> bool:
        """
        Parse package data

        :param data:    data package received
        :param context: return with package head and results from body
        :return: False on failed
        """
        # 1. parse STUN package
        pack = Package.parse(data=data)
        if pack is None:
            self.info('failed to parse package data (%d bytes): %s' % (len(data), data))
            return False
        # 2. parse attributes
        attributes = Attribute.parse_attributes(data=pack.body)
        for item in attributes:
            # 3. process attribute
            self.parse_attribute(attribute=item, context=context)
        context['head'] = pack.head
        return True
