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

from typing import Optional

from udp.tlv import Value

from .tlv import VarName
from .tlv import Field, FieldsValue
from .tlv import BinaryValue, StringValue, TimestampValue
from .tlv import s_value_parsers

from .address import SourceAddressValue, MappedAddressValue, RelayedAddressValue


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
    pass


class WhoCommand(Command):

    @classmethod
    def new(cls) -> Command:
        return cls(tag=Who)


class HelloCommand(Command):

    @classmethod
    def new(cls, location: Value=None, identifier: str=None,
            source_address=None, mapped_address=None, relayed_address=None,
            timestamp: int=0, signature: bytes=None, nat: str=None) -> Command:
        if location is None:
            assert identifier is not None, 'user ID empty'
            location = LocationValue.new(identifier=identifier,
                                         source_address=source_address,
                                         mapped_address=mapped_address,
                                         relayed_address=relayed_address,
                                         timestamp=timestamp, signature=signature, nat=nat)
        return cls(tag=Hello, value=location)


class SignCommand(Command):

    @classmethod
    def new(cls, identifier: str, source_address=None, mapped_address=None, relayed_address=None) -> Command:
        value = LocationValue.new(identifier=identifier,
                                  source_address=source_address,
                                  mapped_address=mapped_address,
                                  relayed_address=relayed_address)
        return cls(tag=Sign, value=value)


class CallCommand(Command):

    @classmethod
    def new(cls, identifier: str) -> Command:
        value = LocationValue.new(identifier=identifier)
        return cls(tag=Call, value=value)


class FromCommand(Command):

    @classmethod
    def new(cls, location: Value=None, identifier: str=None) -> Command:
        if location is None:
            assert identifier is not None, 'UID should not be empty'
            location = LocationValue.new(identifier=identifier)
        return cls(tag=From, value=location)


class ByeCommand(Command):

    @classmethod
    def new(cls, location: Value) -> Command:
        return cls(tag=Bye, value=location)


"""
    Command Values
    ~~~~~~~~~~~~~~
"""


class CommandValue(FieldsValue):

    def __init__(self, fields: list, data: bytes=None):
        self.__id: str = None
        super().__init__(fields=fields, data=data)

    @property
    def identifier(self) -> str:
        return self.__id

    def _set_field(self, field: Field):
        if field.tag == ID:
            f_value = field.value
            assert isinstance(f_value, StringValue), 'ID value error: %s' % f_value
            self.__id = f_value.string
        else:
            clazz = self.__class__.__name__
            print('%s> unknown field: %s -> %s' % (clazz, field.tag, field.value))

    @classmethod
    def new(cls, identifier: str):
        f_id = Field(tag=ID, value=StringValue(string=identifier))
        return cls(fields=[f_id])


class LocationValue(CommandValue):
    """
        Defined for 'HI', 'SIGN', 'FROM' commands to show the user's location
    """

    def __init__(self, fields: list, data: bytes=None):
        self.__source_address: SourceAddressValue = None    # local IP and port
        self.__mapped_address: MappedAddressValue = None    # public IP and port
        self.__relayed_address: RelayedAddressValue = None  # server IP and port
        self.__timestamp: int = 0                           # time for signature
        self.__signature: bytes = None                      # sign(addresses + timestamp)
        self.__nat: str = None
        super().__init__(fields=fields, data=data)

    @property
    def source_address(self) -> Optional[SourceAddressValue]:
        return self.__source_address

    @property
    def mapped_address(self) -> Optional[MappedAddressValue]:
        return self.__mapped_address

    @property
    def relayed_address(self) -> Optional[RelayedAddressValue]:
        return self.__relayed_address

    @property
    def timestamp(self) -> int:
        return self.__timestamp

    @property
    def signature(self) -> Optional[bytes]:
        return self.__signature

    @property
    def nat(self) -> Optional[str]:
        return self.__nat

    def _set_field(self, field: Field):
        f_type = field.tag
        f_value = field.value
        if f_type == SourceAddress:
            assert isinstance(f_value, SourceAddressValue), 'source address error: %s' % f_value
            self.__source_address = f_value
        elif f_type == MappedAddress:
            assert isinstance(f_value, MappedAddressValue), 'mapped address error: %s' % f_value
            self.__mapped_address = f_value
        elif f_type == RelayedAddress:
            assert isinstance(f_value, RelayedAddressValue), 'relayed address error: %s' % f_value
            self.__relayed_address = f_value
        elif f_type == Time:
            assert isinstance(f_value, TimestampValue), 'time value error: %s' % f_value
            self.__timestamp = f_value.value
        elif f_type == Signature:
            assert isinstance(f_value, BinaryValue), 'signature value error: %s' % f_value
            self.__signature = f_value.data
        elif f_type == NAT:
            assert isinstance(f_value, StringValue), 'NAT value error: %s' % f_value
            self.__nat = f_value.string
        else:
            super()._set_field(field=field)

    @classmethod
    def new(cls, identifier: str, source_address=None, mapped_address=None, relayed_address=None,
            timestamp: int=0, signature: bytes=None, nat: str=None):
        f_id = Field(tag=ID, value=StringValue(string=identifier))
        fields = [f_id]
        # append SOURCE-ADDRESS
        if source_address is not None:
            if isinstance(source_address, SourceAddressValue):
                value = source_address
            else:
                assert isinstance(source_address, tuple), 'source address error: %s' % source_address
                value = SourceAddressValue(ip=source_address[0], port=source_address[1])
            f_src = Field(tag=SourceAddress, value=value)
            fields.append(f_src)
        # append MAPPED-ADDRESS
        if mapped_address is not None:
            if isinstance(mapped_address, MappedAddressValue):
                value = mapped_address
            else:
                assert isinstance(mapped_address, tuple), 'mapped address error: %s' % mapped_address
                value = MappedAddressValue(ip=mapped_address[0], port=mapped_address[1])
            f_src = Field(tag=MappedAddress, value=value)
            fields.append(f_src)
        # append RELAYED-ADDRESS
        if relayed_address is not None:
            if isinstance(relayed_address, RelayedAddressValue):
                value = relayed_address
            else:
                assert isinstance(relayed_address, tuple), 'relayed address error: %s' % relayed_address
                value = RelayedAddressValue(ip=relayed_address[0], port=relayed_address[1])
            f_src = Field(tag=RelayedAddress, value=value)
            fields.append(f_src)
        if source_address is not None or mapped_address is not None or relayed_address is not None:
            # append sign time
            if timestamp > 0:
                f_time = Field(tag=Time, value=TimestampValue(value=timestamp))
                fields.append(f_time)
            # append signature
            if signature is not None:
                f_sign = Field(tag=Signature, value=BinaryValue(data=signature))
                fields.append(f_sign)
            # append NAT type
            if nat is not None:
                f_nat = Field(tag=NAT, value=StringValue(string=nat))
                fields.append(f_nat)
        return cls(fields=fields)


# command names
Who = VarName(name='WHO')          # (S) location not found, ask receiver to say 'HI'
Hello = VarName(name='HI')         # (C) login with ID
Sign = VarName(name='SIGN')        # (S) ask client to login
Call = VarName(name='CALL')        # (C) ask server to help connecting with another user
From = VarName(name='FROM')        # (S) help users connecting
Bye = VarName(name='BYE')          # (C) logout with ID and address

# field names
ID = VarName(name='ID')                           # user ID
SourceAddress = VarName(name='SOURCE-ADDRESS')    # source-address (local IP and port)
MappedAddress = VarName(name='MAPPED-ADDRESS')    # mapped-address (public IP and port)
RelayedAddress = VarName(name='RELAYED-ADDRESS')  # relayed-address (server IP and port)
Time = VarName(name='TIME')                       # timestamp (uint32) stored in network order (big endian)
Signature = VarName(name='SIGNATURE')             # verify with ('ADDR' + 'TIME') and meta.key
NAT = VarName(name='NAT')                         # NAT type


# classes for parsing value
s_value_parsers[Hello] = LocationValue
s_value_parsers[Sign] = LocationValue
s_value_parsers[Call] = CommandValue
s_value_parsers[From] = LocationValue
s_value_parsers[Bye] = LocationValue

s_value_parsers[ID] = StringValue
s_value_parsers[SourceAddress] = SourceAddressValue
s_value_parsers[MappedAddress] = MappedAddressValue
s_value_parsers[RelayedAddress] = RelayedAddressValue
s_value_parsers[Time] = TimestampValue
s_value_parsers[Signature] = BinaryValue
s_value_parsers[NAT] = StringValue
