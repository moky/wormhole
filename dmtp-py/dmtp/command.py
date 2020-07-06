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

from udp.tlv import Data

from .tlv import Field, FieldName, FieldValue
from .values import BinaryValue, StringValue, TimestampValue

from .address import SourceAddressValue, MappedAddressValue, RelayedAddressValue
from .values import CommandValue, LocationValue


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
    WHO = FieldName(name='WHO')    # (S) location not found, ask receiver to say 'HI'
    HELLO = FieldName(name='HI')   # (C) login with ID
    SIGN = FieldName(name='SIGN')  # (S) ask client to login
    CALL = FieldName(name='CALL')  # (C) ask server to help connecting with another user
    FROM = FieldName(name='FROM')  # (S) help users connecting
    BYE = FieldName(name='BYE')    # (C) logout with ID and address


class WhoCommand(Command):

    @classmethod
    def new(cls) -> Command:
        return cls(tag=cls.WHO)


class HelloCommand(Command):

    @classmethod
    def new(cls, location: LocationValue=None,
            identifier: Union[str, StringValue]=None,
            source_address: Union[tuple, SourceAddressValue]=None,
            mapped_address: Union[tuple, MappedAddressValue]=None,
            relayed_address: Union[tuple, RelayedAddressValue]=None,
            timestamp: Union[int, TimestampValue]=None,
            signature: Union[bytes, bytearray, Data, BinaryValue]=None,
            nat: Union[str, StringValue]=None) -> Command:
        # check location
        if location is None:
            assert identifier is not None, 'user ID empty'
            location = LocationValue.new(identifier=identifier,
                                         source_address=source_address,
                                         mapped_address=mapped_address,
                                         relayed_address=relayed_address,
                                         timestamp=timestamp, signature=signature, nat=nat)
        return cls(tag=cls.HELLO, value=location)


class SignCommand(Command):

    @classmethod
    def new(cls, identifier: Union[str, StringValue],
            source_address: Union[tuple, SourceAddressValue]=None,
            mapped_address: Union[tuple, MappedAddressValue]=None,
            relayed_address: Union[tuple, RelayedAddressValue]=None) -> Command:
        # create location
        value = LocationValue.new(identifier=identifier,
                                  source_address=source_address,
                                  mapped_address=mapped_address,
                                  relayed_address=relayed_address)
        return cls(tag=cls.SIGN, value=value)


class CallCommand(Command):

    @classmethod
    def new(cls, identifier: Union[str, StringValue]) -> Command:
        value = LocationValue.new(identifier=identifier)
        return cls(tag=cls.CALL, value=value)


class FromCommand(Command):

    @classmethod
    def new(cls, location: LocationValue=None, identifier: Union[str, StringValue]=None) -> Command:
        if location is None:
            assert identifier is not None, 'UID should not be empty'
            location = LocationValue.new(identifier=identifier)
        return cls(tag=cls.FROM, value=location)


class ByeCommand(Command):

    @classmethod
    def new(cls, location: LocationValue) -> Command:
        return cls(tag=cls.BYE, value=location)


# classes for parsing command field
FieldValue.register(tag=Command.HELLO, value_class=LocationValue)
FieldValue.register(tag=Command.SIGN, value_class=LocationValue)
FieldValue.register(tag=Command.CALL, value_class=CommandValue)
FieldValue.register(tag=Command.FROM, value_class=LocationValue)
FieldValue.register(tag=Command.BYE, value_class=LocationValue)

# classes for parsing other field
FieldValue.register(tag=Field.ID, value_class=StringValue)
FieldValue.register(tag=Field.SOURCE_ADDRESS, value_class=SourceAddressValue)
FieldValue.register(tag=Field.MAPPED_ADDRESS, value_class=MappedAddressValue)
FieldValue.register(tag=Field.RELAYED_ADDRESS, value_class=RelayedAddressValue)
FieldValue.register(tag=Field.TIME, value_class=TimestampValue)
FieldValue.register(tag=Field.SIGNATURE, value_class=BinaryValue)
FieldValue.register(tag=Field.NAT, value_class=StringValue)
