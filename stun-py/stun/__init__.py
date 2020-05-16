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

from .protocol import MessageType, MessageLength, TransactionID
from .protocol import Header, Package
from .protocol import BindRequest, BindResponse, BindErrorResponse
from .protocol import SharedSecretRequest, SharedSecretResponse, SharedSecretErrorResponse

from .attributes import Attribute, AttributeType, AttributeLength, AttributeValue
from .attributes import MappedAddress, MappedAddressValue
from .attributes import ResponseAddress, ResponseAddressValue
from .attributes import ChangeRequest, ChangeRequestValue, ChangeIP, ChangePort, ChangeIPAndPort
from .attributes import ChangedAddress, ChangedAddressValue
from .attributes import SourceAddress, SourceAddressValue
from .attributes import Username
from .attributes import Password
from .attributes import MessageIntegrity
from .attributes import ErrorCode
from .attributes import UnknownAttributes
from .attributes import ReflectedFrom
from .attributes import Realm
from .attributes import Nonce
from .attributes import XorMappedAddress, XorMappedAddressValue
from .attributes import XorOnly
from .attributes import Software
from .attributes import AlternateServer
from .attributes import Fingerprint

from .service import Client, Server

name = "STUN"

__author__ = 'Albert Moky'

__all__ = [

    #
    #  Protocol
    #
    'MessageType', 'MessageLength', 'TransactionID',
    'Header', 'Package',
    # message types
    'BindRequest', 'BindResponse', 'BindErrorResponse',
    'SharedSecretRequest', 'SharedSecretResponse', 'SharedSecretErrorResponse',

    #
    #  Attributes
    #
    'Attribute', 'AttributeType', 'AttributeLength', 'AttributeValue',
    # attribute types
    'MappedAddress', 'ResponseAddress', 'ChangeRequest',
    'SourceAddress', 'ChangedAddress',
    'Username', 'Password', 'MessageIntegrity', 'ErrorCode', 'UnknownAttributes', 'ReflectedFrom',
    'Realm', 'Nonce', 'XorMappedAddress', 'XorOnly',
    'Software', 'AlternateServer', 'Fingerprint',
    # attribute values
    'MappedAddressValue', 'ResponseAddressValue',
    'ChangeRequestValue', 'ChangeIP', 'ChangePort', 'ChangeIPAndPort',
    'SourceAddressValue', 'ChangedAddressValue',
    'XorMappedAddressValue',

    #
    #  Service
    #
    'Client', 'Server',
]
