# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
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

from typing import Union, Optional

from udp.data import Data
from udp.data import bytes_to_int, uint8_to_bytes, uint16_to_bytes
from udp.tlv import Type, Value, Length

from .tlv import VarName
from .tlv import Field, FieldsValue
from .tlv import BinaryValue, StringValue
from .tlv import s_value_parsers


"""
    Commands
    ~~~~~~~~

    HI, HELLO
        Send 'ID', 'ADDR', 'S' to the server to tell it where you are from;
        When connecting to the network, send only 'ID' to the server, if got a
        'SIGN' command with MAPPED-ADDRESS responds from a server, sign it and
        send back to the server as login.

        Fields:
            ID - current user's identifier
            ADDR - current user's public IP and port (OPTIONAL)
            S - signature of ADDR (OPTIONAL)
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
            S - signature of ADDR which signed by user (OPTIONAL)
            NAT - user's NAT type (OPTIONAL)

    PROFILE
        Ask the receiver to offer user profile info (includes meta, via message)

        Field:
            ID - user identifier
"""


class Command(Field):

    def __init__(self, t: Type, v: Union[Value, Data, bytes], data: bytes = None):
        if v is not None:
            if isinstance(v, bytes):
                v = Value(data=v)
            elif not isinstance(v, Value):
                assert isinstance(v, Data), 'value error: %s' % v
                v = Value(data=v.data)
        super().__init__(data=data, t=t, v=v)

    def __str__(self):
        clazz = self.__class__.__name__
        return '<%s: %s=%s />' % (clazz, self.type, self.data)


class CommandValue(FieldsValue):

    def __init__(self, fields: list, data: bytes=None):
        self.__id: str = None
        super().__init__(fields=fields, data=data)

    @property
    def id(self) -> str:
        return self.__id

    def _set_field(self, field: Field):
        if field.type == ID:
            f_value = field.value
            assert isinstance(f_value, StringValue), 'ID value error: %s' % f_value
            self.__id = f_value.string
        else:
            clazz = self.__class__.__name__
            print('%s: unknown field "%s" -> "%s"' % (clazz, field.type, field.value))


class LocationValue(CommandValue):
    """
        Defined for 'HI', 'SIGN', 'FROM' commands to show the user's location
    """

    def __init__(self, fields: list, data: bytes=None):
        self.__ip: str = None
        self.__port: int = 0
        self.__address: bytes = None
        self.__signature: bytes = None
        self.__nat: str = None
        super().__init__(fields=fields, data=data)

    @property
    def ip(self) -> Optional[str]:
        return self.__ip

    @property
    def port(self) -> Optional[int]:
        return self.__port

    @property
    def address(self) -> Optional[bytes]:
        return self.__address

    @property
    def signature(self) -> Optional[bytes]:
        return self.__signature

    @property
    def nat(self) -> Optional[str]:
        return self.__nat

    def _set_field(self, field: Field):
        f_type = field.type
        f_value = field.value
        if f_type == Address:
            assert isinstance(f_value, MappedAddressValue), 'Address value error: %s' % f_value
            self.__ip = f_value.ip
            self.__port = f_value.port
            self.__address = f_value.data
        elif f_type == Signature:
            self.__signature = f_value.data
        elif f_type == NAT:
            assert isinstance(f_value, StringValue), 'NAT value error: %s' % f_value
            self.__nat = f_value.string
        else:
            super()._set_field(field=field)

    @classmethod
    def new(cls, uid: str, ip: str=None, port: int=0, signature: bytes=None, nat: str=None):
        f_id = Field(t=ID, v=StringValue(string=uid))
        fields = [f_id]
        # append MAPPED-ADDRESS
        if ip is not None and port > 0:
            f_addr = Field(t=Address, v=MappedAddressValue(ip=ip, port=port))
            fields.append(f_addr)
        # append signature
        if signature is not None:
            f_sign = Field(t=Signature, v=BinaryValue(data=signature))
            fields.append(f_sign)
        # append NAT type
        if nat is not None:
            f_nat = Field(t=NAT, v=StringValue(string=nat))
            fields.append(f_nat)
        return cls(fields=fields)


class MappedAddressValue(Value):

    family_ipv4 = 0x01
    family_ipv6 = 0x02

    def __init__(self, ip: str, port: int, family: int=0x01, data: bytes=None):
        if data is None:
            ip_data = self.ip_to_bytes(ip=ip, family=family)
            port_data = uint16_to_bytes(value=port)
            family_data = uint8_to_bytes(value=family)
            data = b'\0' + family_data + port_data + ip_data
        super().__init__(data=data)
        self.__ip = ip
        self.__port = port

    def __str__(self):
        return '"%s:%d"' % (self.ip, self.port)

    def __repr__(self):
        return '"%s:%d"' % (self.ip, self.port)

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def port(self) -> int:
        return self.__port

    @classmethod
    def ip_to_bytes(cls, ip: str, family: int) -> bytes:
        if family == cls.family_ipv4:
            # IPv4
            array = ip.split('.')
            assert len(array) == 4, 'IP address error: %s' % ip
            return bytes([int(x) for x in array])
            pass
        elif family == cls.family_ipv6:
            # TODO: IPv6
            assert False, 'implement me!'
        else:
            raise ValueError('unknown address family: %d' % family)

    @classmethod
    def bytes_to_ip(cls, address: bytes, family: int) -> str:
        # check address family
        if family == cls.family_ipv4:
            assert len(address) == 4, 'IPv4 data error: %s' % address
            # IPv4
            return '.'.join([
                str(bytes_to_int(address[0:1])),
                str(bytes_to_int(address[1:2])),
                str(bytes_to_int(address[2:3])),
                str(bytes_to_int(address[3:4])),
            ])
        elif family == cls.family_ipv6:
            assert len(address) == 16, 'IPv6 data error: %s' % address
            # TODO: IPv6
            assert False, 'implement me!'
        else:
            raise ValueError('unknown address family: %d' % family)

    @classmethod
    def parse(cls, data: bytes, t: Type, length: Length=None):
        assert len(data) >= 8, 'mapped-address value error: %s' % data
        if data[0] != 0:
            return None
        family = bytes_to_int(data[1:2])
        port = bytes_to_int(data[2:4])
        ip = cls.bytes_to_ip(address=data[4:], family=family)
        return cls(data=data, ip=ip, port=port, family=family)


# command names
Login = VarName(name='HI')
Sign = VarName(name='SIGN')
Call = VarName(name='CALL')
From = VarName(name='FROM')
Profile = VarName(name='PROFILE')

# field names
ID = VarName(name='ID')
Address = VarName(name='ADDR')  # mapped-address
Signature = VarName(name='V')   # verify with 'ADDR' and meta.key
NAT = VarName(name='NAT')       # NAT type


# classes for parsing value
s_value_parsers[Login] = LocationValue
s_value_parsers[Sign] = LocationValue
s_value_parsers[Call] = CommandValue
s_value_parsers[From] = LocationValue
s_value_parsers[Profile] = CommandValue

s_value_parsers[ID] = StringValue
s_value_parsers[Address] = MappedAddressValue
s_value_parsers[Signature] = BinaryValue
s_value_parsers[NAT] = StringValue
