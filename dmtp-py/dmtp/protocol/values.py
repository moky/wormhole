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

from typing import Optional, Union, List

from udp.ba import ByteArray
from stun import MappedAddressValue, SourceAddressValue

from ..tlv import Field, FieldName
from ..tlv import MapValue, StringValue, BinaryValue, TimestampValue

from .address import RelayedAddressValue


"""
    Command Values
    ~~~~~~~~~~~~~~
"""


class CommandValue(MapValue):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], fields: List[Field]):
        super().__init__(data=data, fields=fields)
        self.__id = None

    @property
    def identifier(self) -> str:
        if self.__id is None:
            self.__id = self.get_string_value(tag=Field.ID)
        return self.__id

    @classmethod
    def from_id(cls, identifier: str):
        value = StringValue.new(string=identifier)
        f_id = Field.new(tag=Field.ID, value=value)
        return cls.from_fields(fields=[f_id])


class LocationValue(CommandValue):
    """
        Defined for 'HI', 'SIGN', 'FROM' commands to show the user's location
    """

    def __init__(self, data: Union[bytes, bytearray, ByteArray], fields: List[Field]):
        super().__init__(data=data, fields=fields)
        self.__source_address: Optional[tuple] = None   # local IP and port
        self.__mapped_address: Optional[tuple] = None   # public IP and port
        self.__relayed_address: Optional[tuple] = None  # server IP and port
        self.__timestamp: Optional[int] = None          # time for signature
        self.__signature: Optional[bytes] = None         # sign(addresses + timestamp)
        self.__nat: Optional[str] = None                # NAT type

    def get_address_value(self, tag: FieldName, default: tuple = None) -> Optional[tuple]:
        value = self.get(tag)
        if isinstance(value, MappedAddressValue):
            return value.ip, value.port
        else:
            return default

    @property
    def source_address(self) -> Optional[tuple]:
        if self.__source_address is None:
            self.__source_address = self.get_address_value(tag=Field.SOURCE_ADDRESS)
        return self.__source_address

    @property
    def mapped_address(self) -> Optional[tuple]:
        if self.__mapped_address is None:
            self.__mapped_address = self.get_address_value(tag=Field.MAPPED_ADDRESS)
        return self.__mapped_address

    @property
    def relayed_address(self) -> Optional[tuple]:
        if self.__relayed_address is None:
            self.__relayed_address = self.get_address_value(tag=Field.RELAYED_ADDRESS)
        return self.__relayed_address

    @property
    def timestamp(self) -> int:
        if self.__timestamp is None:
            self.__timestamp = self.get_int_value(tag=Field.TIME)
        return self.__timestamp

    @property
    def signature(self) -> Optional[bytes]:
        if self.__signature is None:
            self.__signature = self.get_binary_value(tag=Field.SIGNATURE)
        return self.__signature

    @property
    def nat(self) -> Optional[str]:
        if self.__nat is None:
            self.__nat = self.get_string_value(tag=Field.NAT)
        return self.__nat

    @classmethod
    def new(cls, identifier: Union[str, StringValue],
            source_address: Union[tuple, SourceAddressValue] = None,
            mapped_address: Union[tuple, MappedAddressValue] = None,
            relayed_address: Union[tuple, RelayedAddressValue] = None,
            timestamp: Union[int, TimestampValue] = None,
            signature: Union[bytes, bytearray, ByteArray] = None,
            nat: Union[str, StringValue] = None):
        # ID
        if isinstance(identifier, str):
            identifier = StringValue.new(string=identifier)
        f_id = Field.new(tag=Field.ID, value=identifier)
        fields = [f_id]
        # append SOURCE-ADDRESS
        if source_address is not None:
            if isinstance(source_address, tuple):
                source_address = SourceAddressValue.new(ip=source_address[0], port=source_address[1])
            f_address = Field.new(tag=Field.SOURCE_ADDRESS, value=source_address)
            fields.append(f_address)
        # append MAPPED-ADDRESS
        if mapped_address is not None:
            if isinstance(mapped_address, tuple):
                mapped_address = MappedAddressValue.new(ip=mapped_address[0], port=mapped_address[1])
            f_address = Field.new(tag=Field.MAPPED_ADDRESS, value=mapped_address)
            fields.append(f_address)
        # append RELAYED-ADDRESS
        if relayed_address is not None:
            if isinstance(relayed_address, tuple):
                relayed_address = RelayedAddressValue.new(ip=relayed_address[0], port=relayed_address[1])
            f_address = Field.new(tag=Field.RELAYED_ADDRESS, value=relayed_address)
            fields.append(f_address)
        # append sign time
        if timestamp is not None:
            if isinstance(timestamp, int):
                timestamp = TimestampValue.new(value=timestamp)
            f_time = Field.new(tag=Field.TIME, value=timestamp)
            fields.append(f_time)
        # append signature
        if signature is not None:
            if not isinstance(signature, BinaryValue):
                # bytes, bytearray or ByteArray
                signature = BinaryValue(data=signature)
            f_sign = Field.new(tag=Field.SIGNATURE, value=signature)
            fields.append(f_sign)
        # append NAT type
        if nat is not None:
            if isinstance(nat, str):
                nat = StringValue.new(string=nat)
            f_nat = Field.new(tag=Field.NAT, value=nat)
            fields.append(f_nat)
        return cls.from_fields(fields=fields)
