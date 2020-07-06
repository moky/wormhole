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

from typing import Optional, Union

from udp.tlv import Data, MutableData, UInt8Data, UInt32Data

from .tlv import Field, FieldName, FieldLength, FieldValue
from .address import SourceAddressValue, MappedAddressValue, RelayedAddressValue


class FieldsValue(FieldValue, dict):

    def __init__(self, fields: list, data: Data=None):
        if data is None:
            length = 0
            for item in fields:
                assert isinstance(item, Field), 'field item error: %s' % item
                length += item.length
            data = MutableData(capacity=length)
            for item in fields:
                assert isinstance(item, Field), 'field item error: %s' % item
                data.append(item)
        super().__init__(data=data)
        # set fields
        for item in fields:
            assert isinstance(item, Field), 'field item error: %s' % item
            name = item.tag
            value = item.value
            assert isinstance(name, FieldName), 'field name error: %s' % name
            assert value is None or isinstance(value, FieldValue), 'field value error: %s' % value
            self._set_field(tag=name, value=value)
        self.__fields = fields

    def _set_field(self, tag: FieldName, value: FieldValue):
        name = tag.name
        if value is None:
            self.pop(name, None)
        elif isinstance(value, StringValue):
            self[name] = value.string
        elif isinstance(value, ByteValue):
            self[name] = value.value
        elif isinstance(value, TimestampValue):
            self[name] = value.value
        elif isinstance(value, BinaryValue):
            self[name] = value
        else:
            clazz = self.__class__.__name__
            print('%s> unknown field: %s -> %s' % (clazz, tag, value))

    @classmethod
    def parse(cls, data: Data, tag: FieldName, length: FieldLength=None):
        # parse fields
        fields = Field.parse_all(data=data)
        return cls(data=data, fields=fields)


class BinaryValue(FieldValue):

    def __str__(self):
        return '%s' % self.get_bytes()

    def __repr__(self):
        return '%s' % self.get_bytes()


class ByteValue(UInt8Data, FieldValue):
    pass


class TimestampValue(UInt32Data, FieldValue):
    pass


class StringValue(FieldValue):

    def __init__(self, string: str, data: Data=None):
        if data is None:
            data = Data(data=string.encode('utf-8'))
        super().__init__(data=data)
        self.__string = string

    def __str__(self):
        return self.__string

    def __repr__(self):
        return self.__string

    @property
    def string(self) -> str:
        return self.__string

    @classmethod
    def parse(cls, data: Data, tag: FieldName, length: FieldLength=None):
        # parse string value
        value = data.get_bytes()
        string = value.decode('utf-8')
        return cls(string=string, data=data)


"""
    Command Values
    ~~~~~~~~~~~~~~
"""


class CommandValue(FieldsValue):

    def __init__(self, fields: list, data: Data=None):
        super().__init__(fields=fields, data=data)
        self.__id: str = None

    @property
    def identifier(self) -> str:
        if self.__id is None:
            self.__id = self.get(Field.ID)
        return self.__id

    @classmethod
    def new(cls, identifier: str):
        f_id = Field(tag=Field.ID, value=StringValue(string=identifier))
        return cls(fields=[f_id])


class LocationValue(CommandValue):
    """
        Defined for 'HI', 'SIGN', 'FROM' commands to show the user's location
    """

    def __init__(self, fields: list, data: bytes=None):
        super().__init__(fields=fields, data=data)
        self.__source_address: tuple = None   # local IP and port
        self.__mapped_address: tuple = None   # public IP and port
        self.__relayed_address: tuple = None  # server IP and port
        self.__timestamp: int = None          # time for signature
        self.__signature: Data = None         # sign(addresses + timestamp)
        self.__nat: str = None                # NAT type

    @property
    def source_address(self) -> Optional[tuple]:
        if self.__source_address is None:
            self.__source_address = self.get(Field.SOURCE_ADDRESS)
        return self.__source_address

    @property
    def mapped_address(self) -> Optional[tuple]:
        if self.__mapped_address is None:
            self.__mapped_address = self.get(Field.MAPPED_ADDRESS)
        return self.__mapped_address

    @property
    def relayed_address(self) -> Optional[tuple]:
        if self.__relayed_address is None:
            self.__relayed_address = self.get(Field.RELAYED_ADDRESS)
        return self.__relayed_address

    @property
    def timestamp(self) -> Optional[int]:
        if self.__timestamp is None:
            self.__timestamp = self.get(Field.TIME, 0)
        return self.__timestamp

    @property
    def signature(self) -> Optional[Data]:
        if self.__signature is None:
            self.__signature = self.get(Field.SIGNATURE)
        return self.__signature

    @property
    def nat(self) -> Optional[str]:
        if self.__nat is None:
            self.__nat = self.get(Field.NAT)
        return self.__nat

    def _set_field(self, tag: FieldName, value: FieldValue):
        name = tag.name
        if value is None:
            self.pop(name, None)
        elif isinstance(value, MappedAddressValue):
            self[name] = (value.ip, value.port)
        else:
            super()._set_field(tag=tag, value=value)

    @classmethod
    def new(cls, identifier: Union[str, StringValue],
            source_address: Union[tuple, SourceAddressValue]=None,
            mapped_address: Union[tuple, MappedAddressValue]=None,
            relayed_address: Union[tuple, RelayedAddressValue]=None,
            timestamp: Union[int, TimestampValue]=None,
            signature: Union[bytes, bytearray, Data, BinaryValue]=None,
            nat: Union[str, StringValue]=None):
        # ID
        if isinstance(identifier, str):
            identifier = StringValue(string=identifier)
        f_id = Field(tag=Field.ID, value=identifier)
        fields = [f_id]
        # append SOURCE-ADDRESS
        if source_address is not None:
            if isinstance(source_address, tuple):
                source_address = SourceAddressValue(ip=source_address[0], port=source_address[1])
            f_address = Field(tag=Field.SOURCE_ADDRESS, value=source_address)
            fields.append(f_address)
        # append MAPPED-ADDRESS
        if mapped_address is not None:
            if isinstance(mapped_address, tuple):
                mapped_address = MappedAddressValue(ip=mapped_address[0], port=mapped_address[1])
            f_address = Field(tag=Field.MAPPED_ADDRESS, value=mapped_address)
            fields.append(f_address)
        # append RELAYED-ADDRESS
        if relayed_address is not None:
            if isinstance(relayed_address, tuple):
                relayed_address = RelayedAddressValue(ip=relayed_address[0], port=relayed_address[1])
            f_address = Field(tag=Field.RELAYED_ADDRESS, value=relayed_address)
            fields.append(f_address)
        # append sign time
        if timestamp is not None:
            if isinstance(timestamp, int):
                timestamp = TimestampValue(value=timestamp)
            f_time = Field(tag=Field.TIME, value=timestamp)
            fields.append(f_time)
        # append signature
        if signature is not None:
            if not isinstance(signature, BinaryValue):
                # bytes, bytearray or Data
                signature = BinaryValue(data=signature)
            f_sign = Field(tag=Field.SIGNATURE, value=signature)
            fields.append(f_sign)
        # append NAT type
        if nat is not None:
            if isinstance(nat, str):
                nat = StringValue(string=nat)
            f_nat = Field(tag=Field.NAT, value=nat)
            fields.append(f_nat)
        return cls(fields=fields)
