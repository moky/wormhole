# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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

from abc import ABC
from typing import Optional, Union, Dict, Generic

from udp.ba import ByteArray
from stun.tlv import TagParser
from stun.tlv import LengthParser, VarLength as FieldLength
from stun.tlv import Value as FieldValue, ValueParser, RawValue
from stun.tlv import Triad, Parser as TriadParser
from stun.tlv.entry import E

from .tag import StringTag as FieldName


class Field(Triad[FieldName, FieldLength, FieldValue]):

    # field names
    ID = FieldName.from_str(name='ID')                            # user ID
    SOURCE_ADDRESS = FieldName.from_str(name='SOURCE-ADDRESS')    # source-address (local IP and port)
    MAPPED_ADDRESS = FieldName.from_str(name='MAPPED-ADDRESS')    # mapped-address (public IP and port)
    RELAYED_ADDRESS = FieldName.from_str(name='RELAYED-ADDRESS')  # relayed-address (server IP and port)
    TIME = FieldName.from_str(name='TIME')                        # timestamp (uint32, network order, big endian)
    SIGNATURE = FieldName.from_str(name='SIGNATURE')              # verify with ('ADDR' + 'TIME') and meta.key
    NAT = FieldName.from_str(name='NAT')                          # NAT type

    @classmethod
    def new(cls, tag: FieldName, length: Optional[FieldLength] = None, value: Optional[FieldValue] = None):  # -> Field
        if value is None:
            value = RawValue.ZERO
            length = FieldLength.ZERO
        elif length is None:
            length = FieldLength.from_int(value=value.size)
        data = tag.concat(length).concat(value)
        return cls(data=data, tag=tag, length=length, value=value)

    @classmethod
    def parse_fields(cls, data: ByteArray):  # -> List[Field]
        return get_parser('field_parser').parse_entries(data=data)

    @classmethod
    def get_parser(cls, name: str) -> TriadParser:
        return get_parser(name=name)

    @classmethod
    def set_parser(cls, name: str, parser: TriadParser):
        set_parser(name=name, parser=parser)

    @classmethod
    def register(cls, tag: FieldName, parser: ValueParser[FieldName, FieldLength, FieldValue]):
        """ Register ValueParser """
        set_parser(name=tag.name, parser=parser)


class FieldParser(TriadParser[E, FieldName, FieldLength, FieldValue],
                  TagParser[FieldName],
                  LengthParser[FieldName, FieldLength],
                  ValueParser[FieldName, FieldLength, FieldValue],
                  Generic[E], ABC):

    @property
    def tag_parser(self) -> TagParser[FieldName]:
        return self

    @property
    def length_parser(self) -> LengthParser[FieldName, FieldLength]:
        return self

    @property
    def value_parser(self) -> ValueParser[FieldName, FieldLength, FieldValue]:
        return self

    # def create_entry(self, data: ByteArray, tag: FieldName, length: FieldLength, value: FieldValue) -> Field:
    #     return Field(data=data, tag=tag, length=length, value=value)

    def parse_tag(self, data: ByteArray) -> Optional[FieldName]:
        return FieldName.parse(data=data)

    def parse_length(self, data: ByteArray, tag: FieldName) -> Optional[FieldLength]:
        return FieldLength.parse(data=data, tag=tag)

    def parse_value(self, data: ByteArray, tag: FieldName, length: FieldLength) -> Optional[FieldValue]:
        parser = get_parser(tag.name)
        if parser is None:
            return RawValue.parse(data=data, tag=tag, length=length)
        else:
            return parser.parse_value(data=data, tag=tag, length=length)


#
#  FieldParser, ValueParsers
#
def get_parser(name: str) -> Union[TriadParser[Field, FieldName, FieldLength, FieldValue],
                                   ValueParser[FieldName, FieldLength, FieldValue]]:
    return g_parsers.get(name)


def set_parser(name: str, parser: Union[TriadParser[Field, FieldName, FieldLength, FieldValue],
                                        ValueParser[FieldName, FieldLength, FieldValue]]):
    g_parsers[name] = parser


class CommonFieldParser(FieldParser[Field]):
    """ Default FieldParser """

    def create_entry(self, data: ByteArray, tag: FieldName, length: FieldLength, value: FieldValue) -> Field:
        return Field(data=data, tag=tag, length=length, value=value)


g_parsers: Dict[str, Union[TriadParser[Field, FieldName, FieldLength, FieldValue],
                           ValueParser[FieldName, FieldLength, FieldValue]]] = {}

set_parser(name='field_parser', parser=CommonFieldParser())
