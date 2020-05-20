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

from typing import Optional, Union

from udp.data import Data, VarIntData
from udp.data import bytes_to_varint, bytes_to_int
from udp.data import varint_to_bytes, uint8_to_bytes, uint16_to_bytes
from udp.tlv import TLV, Type, Length, Value


class VarName(Type):

    def __init__(self, name: str, data: bytes=None):
        if data is None:
            data = name.encode('utf-8') + b'\0'
        super().__init__(data=data)
        self.__name = name

    def __str__(self):
        return self.__name

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def parse(cls, data: bytes):
        pos = data.find(b'\0')
        if pos < 1:
            return None
        data = data[:pos+1]
        name = data.rstrip(b'\0').decode('utf-8')
        return cls(name=name, data=data)


class VarLength(VarIntData, Length):

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = varint_to_bytes(value)
        super().__init__(data=data, value=value)

    def __str__(self):
        return self.value

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: bytes, t: Type):
        value, length = bytes_to_varint(data=data)
        return cls(data=data[:length], value=value)


class Field(TLV):

    def __init__(self, t: Type, v: Value, data: bytes=None):
        if data is None:
            data = t.data + varint_to_bytes(len(v.data)) + v.data
        super().__init__(data=data, t=t, v=v)

    @classmethod
    def parse_type(cls, data: bytes) -> Optional[VarName]:
        return VarName.parse(data=data)

    @classmethod
    def parse_length(cls, data: bytes, t: Type) -> Optional[VarLength]:
        return VarLength.parse(data=data, t=t)

    @classmethod
    def parse_value(cls, data: bytes, t: Type, length: Length = None) -> Optional[Value]:
        if length is not None:
            # check length
            data_len = len(data)
            if data_len > length.value:
                data = data[:length.value]
            else:
                assert data_len == length.value, 'data length not enough: %d < %d' % (data_len, length.value)
        # get attribute parser with type
        parser = s_value_parsers.get(t)
        if parser is None:
            parser = Value
        return parser.parse(data=data, t=t, length=length)


class FieldsValue(Value):

    def __init__(self, fields: list, data: bytes=None):
        if data is None:
            data = b''
            for item in fields:
                assert isinstance(item, Field), 'field item error: %s' % item
                data += item.data
        super().__init__(data=data)
        # set fields
        self.__fields = fields
        for item in fields:
            self._set_field(item)

    @property
    def fields(self) -> list:
        return self.__fields

    def _set_field(self, field: Field):
        pass

    @classmethod
    def parse(cls, data: bytes, t: Type, length: Length=None):
        if length is None or length.value == 0:
            return None
        else:
            length = length.value
        data_len = len(data)
        if data_len < length:
            return None
        elif data_len > length:
            data = data[:length]
        # parse fields
        fields = Field.parse_all(data=data)
        return cls(fields=fields, data=data)


class StringValue(Value):

    def __init__(self, value: str, data: bytes=None):
        if data is None:
            data = value.encode('utf-8')
        super().__init__(data=data)
        self.__value = value

    def __str__(self):
        return self.__value

    @property
    def value(self) -> str:
        return self.__value

    @classmethod
    def parse(cls, data: bytes, t: Type, length: Length=None):
        if length is None or length.value == 0:
            return None
        else:
            length = length.value
        data_len = len(data)
        if data_len < length:
            return None
        elif data_len > length:
            data = data[:length]
        # parse string value
        value = data.decode('utf-8')
        return cls(value=value, data=data)


"""
    Commands
    ~~~~~~~~
    
    LOGIN
        send 'ID' to a server
        
    SIGN
        respond the user's public address to ask signing
        
    CALL
        request for binding with someone
"""


class Command(Field):

    def __init__(self, t: Type, v: Union[Value, Data, bytes], data: bytes=None):
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


# command names
Login = VarName(name='LOGIN')
Sign = VarName(name='SIGN')
Call = VarName(name='CALL')


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
            self.__id = field.value.value
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


"""
    Fields in Command Value
    ~~~~~~~~~~~~~~~~~~~~~~~
"""

# field names
ID = VarName(name='ID')
Address = VarName(name='ADDR')
Signature = VarName(name='SIGN')


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
        return '%s:%d' % (self.ip, self.port)

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


# classes for parsing value
s_value_parsers = {
    Login: LoginValue,
    Sign: SignValue,
    Call: CallValue,

    ID: StringValue,
    Address: MappedAddressValue,
}
