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

from typing import Union

from udp.data import Data
from udp.data import bytes_to_int, uint8_to_bytes, uint16_to_bytes

from .tlv import *


"""
    Commands
    ~~~~~~~~

    HI
        send 'ID' to the receiver at first time;
        if got a 'SIGN' command with MAPPED-ADDRESS responds from a server,
        sign it and send back to the server for login.

        Fields:
            ID - current user's identifier
            ADDR - current user's public IP and port
            SIGN - signature of ADDR

    PROFILE
        if only contains a field 'ID', means asking you to offer your profile;
        respond your profile with the same command but fill with profile data.

        Fields:
            ID - user identifier
            META - user's meta info
            PROFILE - user's profile info

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
        Server-Client command: deliver the request for a user

        Fields:
            ID - sender identifier
            ADDR - sender's public IP and port
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


class LoginValue(FieldsValue):

    def __init__(self, fields: list, data: bytes=None):
        self.__id: str = None
        self.__ip: str = None
        self.__port: int = 0
        self.__address: bytes = None
        self.__signature: bytes = None
        super().__init__(fields=fields, data=data)

    @property
    def id(self) -> str:
        return self.__id

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def port(self) -> int:
        return self.__port

    @property
    def address(self) -> bytes:
        return self.__address

    @property
    def signature(self) -> bytes:
        return self.__signature

    def _set_field(self, field: Field):
        f_type = field.type
        f_value = field.value
        if f_type == ID:
            assert isinstance(f_value, StringValue), 'ID value error: %s' % f_value
            self.__id = f_value.string
        elif f_type == Address:
            assert isinstance(f_value, MappedAddressValue), 'Address value error: %s' % f_value
            self.__ip = f_value.ip
            self.__port = f_value.port
            self.__address = f_value.data
        elif f_type == Signature:
            self.__signature = f_value.data
        else:
            print('unknown field: %s -> %s' % (f_type, f_value))


class SignValue(FieldsValue):

    def __init__(self, fields: list, data: bytes=None):
        self.__id: str = None
        self.__ip: str = None
        self.__port: int = 0
        self.__address: bytes = None
        super().__init__(fields=fields, data=data)

    @property
    def id(self) -> str:
        return self.__id

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def port(self) -> int:
        return self.__port

    @property
    def address(self) -> bytes:
        return self.__address

    def _set_field(self, field: Field):
        f_type = field.type
        f_value = field.value
        if f_type == ID:
            assert isinstance(f_value, StringValue), 'ID value error: %s' % f_value
            self.__id = field.value.value
        elif f_type == Address:
            assert isinstance(f_value, MappedAddressValue), 'Address value error: %s' % f_value
            self.__ip = f_value.ip
            self.__port = f_value.port
            self.__address = f_value.data
        else:
            print('unknown field: %s -> %s' % (f_type, f_value))


class CallValue(FieldsValue):

    def __init__(self, fields: list, data: bytes=None):
        self.__id: str = None
        super().__init__(fields=fields, data=data)

    @property
    def id(self) -> str:
        return self.__id

    def _set_field(self, field: Field):
        f_type = field.type
        f_value = field.value
        if f_type == ID:
            assert isinstance(f_value, StringValue), 'ID value error: %s' % f_value
            self.__id = field.value.value
        else:
            print('unknown field: %s -> %s' % (f_type, f_value))


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

# field names
ID = VarName(name='ID')
Address = VarName(name='ADDRESS')
Signature = VarName(name='S')


# classes for parsing value
s_value_parsers[Login] = LoginValue
s_value_parsers[Sign] = SignValue
s_value_parsers[Call] = CallValue

s_value_parsers[ID] = StringValue
s_value_parsers[Address] = MappedAddressValue
s_value_parsers[Signature] = BinaryValue
