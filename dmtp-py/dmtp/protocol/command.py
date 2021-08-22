# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
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

from typing import Union

from udp.ba import ByteArray
from stun import SourceAddressValue, MappedAddressValue

from ..tlv import Field, FieldParser
from ..tlv import FieldName, FieldLength, FieldValue
from ..tlv import StringValue, BinaryValue, TimestampValue

from .address import RelayedAddressValue
from .values import LocationValue


"""
    Commands
    ~~~~~~~~
    
    WHO
        Ask the receiver 'Who are you?' for user ID. The receiver should respond
        a 'HI' command with user ID.

    HI (HELLO)
        Send 'ID' to tell the receiver who you are;
        Send 'ID', 'ADDR', 'S' and 'NAT' to the server for login.
        
        When connecting to the network, send only 'ID' to the server, if got a
        'SIGN' command with MAPPED-ADDRESS responds from a server, sign it and
        send back to the server for login.

        Fields:
            ID - current user's identifier
            ADDR - current user's public IP and port (OPTIONAL)
            TIME - current time (OPTIONAL)
            S - signature of 'ADDR+TIME' (OPTIONAL)
            NAT - current user's NAT type (OPTIONAL)

    SIGN
        Server-Client command: respond the user's MAPPED-ADDRESS to ask signing.

        Fields:
            ID - user identifier
            ADDR - user's public IP and port

    CALL
        Client-Server command: ask the server to help connecting with someone.

        Field:
            ID - contact identifier

    FROM
        Server-Client command: deliver the user's location info;
        When the server received a 'CALL' command from user(A), it will check
        whether another user(B) being called is online,
        if YES, send a 'FROM' command to user(B) with the user(A)'s location,
        at the same time, respond to user(A) with the user(B)'s location;
        if NO, respond an empty 'FROM' command with only one field 'ID'.

        Fields:
            ID - user identifier
            ADDR - user's public IP and port (OPTIONAL)
            TIME - signed time (OPTIONAL)
            S - signature of 'ADDR+TIME' signed by this user (OPTIONAL)
            NAT - user's NAT type (OPTIONAL)

    BYE
        When a client is offline, send this command to the server, or broadcast
        this command to every contacts to logout.

        Fields:
            ID - user identifier
            ADDR - user's public IP and port
            TIME - signed time
            S - signature of 'ADDR+TIME' signed by this user
            NAT - user's NAT type (OPTIONAL)
"""


class Command(Field):

    # command names
    WHO = FieldName.from_str(name='WHO')    # (S) location not found, ask receiver to say 'HI'
    HELLO = FieldName.from_str(name='HI')   # (C) login with ID
    SIGN = FieldName.from_str(name='SIGN')  # (S) ask client to login
    CALL = FieldName.from_str(name='CALL')  # (C) ask server to help connecting with another user
    FROM = FieldName.from_str(name='FROM')  # (S) help users connecting
    BYE = FieldName.from_str(name='BYE')    # (C) logout with ID and address

    @classmethod
    def who_command(cls):
        return cls.new(tag=cls.WHO)

    @classmethod
    def hello_command(cls, location: LocationValue = None,
                      identifier: Union[str, StringValue] = None,
                      source_address: Union[tuple, SourceAddressValue] = None,
                      mapped_address: Union[tuple, MappedAddressValue] = None,
                      relayed_address: Union[tuple, RelayedAddressValue] = None,
                      timestamp: Union[int, TimestampValue] = None,
                      signature: Union[bytes, bytearray, ByteArray, BinaryValue] = None,
                      nat: Union[str, StringValue] = None):
        # check location
        if location is None:
            assert identifier is not None, 'user ID empty'
            location = LocationValue.new(identifier=identifier,
                                         source_address=source_address,
                                         mapped_address=mapped_address,
                                         relayed_address=relayed_address,
                                         timestamp=timestamp, signature=signature, nat=nat)
        return cls.new(tag=cls.HELLO, value=location)

    @classmethod
    def sign_command(cls, identifier: Union[str, StringValue],
                     source_address: Union[tuple, SourceAddressValue] = None,
                     mapped_address: Union[tuple, MappedAddressValue] = None,
                     relayed_address: Union[tuple, RelayedAddressValue] = None):
        # create location
        value = LocationValue.new(identifier=identifier,
                                  source_address=source_address,
                                  mapped_address=mapped_address,
                                  relayed_address=relayed_address)
        return cls.new(tag=cls.SIGN, value=value)

    @classmethod
    def call_command(cls, identifier: Union[str, StringValue]):
        value = LocationValue.new(identifier=identifier)
        return cls.new(tag=cls.CALL, value=value)

    @classmethod
    def from_command(cls, location: LocationValue = None, identifier: Union[str, StringValue] = None):
        if location is None:
            assert identifier is not None, 'UID should not be empty'
            location = LocationValue.new(identifier=identifier)
        return cls.new(tag=cls.FROM, value=location)

    @classmethod
    def bye_command(cls, location: LocationValue):
        return cls.new(tag=cls.BYE, value=location)

    @classmethod
    def parse_commands(cls, data: ByteArray):  # -> List[Command]
        return cls.get_parser('command_parser').parse_entries(data=data)


class CommandParser(FieldParser[Command]):
    """ Command Parser """

    def create_entry(self, data: ByteArray, tag: FieldName, length: FieldLength, value: FieldValue) -> Command:
        return Command(data=data, tag=tag, length=length, value=value)


Field.set_parser(name='command_parser', parser=CommandParser())
