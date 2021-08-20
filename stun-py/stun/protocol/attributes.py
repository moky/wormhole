# -*- coding: utf-8 -*-
#
#   STUN: Session Traversal Utilities for NAT
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

"""
    Session Traversal Utilities for NAT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    [RFC] https://www.ietf.org/rfc/rfc5389.txt
    [RFC] https://www.ietf.org/rfc/rfc3489.txt
"""

from typing import Optional, Union, Dict

from udp.ba import ByteArray
from udp.ba import Endian, UInt16Data, Convert

from ..tlv import Tag16, TagParser
from ..tlv import Length16, LengthParser
from ..tlv import Value, RawValue, ValueParser
from ..tlv import Triad, Parser as TriadParser


"""
    STUN Attributes
    ~~~~~~~~~~~~~~~

   After the STUN header are zero or more attributes.  Each attribute
   MUST be TLV encoded, with a 16-bit type, 16-bit length, and value.
   Each STUN attribute MUST end on a 32-bit boundary.  As mentioned
   above, all fields in an attribute are transmitted most significant
   bit first.

       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |         Type                  |            Length             |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Value (variable)                ....
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

                    Figure 4: Format of STUN Attributes
"""


#
#  Attribute Type
#
class AttributeType(Tag16):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], value: int, endian: Endian, name: str):
        super().__init__(data=data, value=value, endian=endian)
        self.__name = name

    def __str__(self):
        return self.__name

    def __repr__(self):
        return self.__name

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Optional[AttributeType]:
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt16Data):
            data = Convert.uint16data_from_data(data=data)
        if data is not None:
            t = cls.__attribute_types.get(data.value)
            if t is None:
                name = 'Attribute-0x%+04X' % data.value
                return create_type(value=data.value, name=name)
            else:
                return t

    @classmethod
    def cache(cls, value: int, attribute_type):
        cls.__attribute_types[value] = attribute_type

    # Attribute Types in STUN message
    __attribute_types = {}  # int -> AttributeType

    # Comprehension-required range (0x0000-0x7FFF)
    # Comprehension-optional range (0x8000-0xFFFF)

    # [RFC-3489]
    MAPPED_ADDRESS = None
    RESPONSE_ADDRESS = None
    CHANGE_REQUEST = None
    SOURCE_ADDRESS = None
    CHANGED_ADDRESS = None
    USERNAME = None
    PASSWORD = None
    MESSAGE_INTEGRITY = None
    ERROR_CODE = None
    UNKNOWN_ATTRIBUTES = None
    REFLECTED_FROM = None

    # [RFC-5389]
    REALM = None
    NONCE = None
    XOR_MAPPED_ADDRESS = None

    XOR_MAPPED_ADDRESS2 = None
    XOR_ONLY = None
    SOFTWARE = None
    ALTERNATE_SERVER = None
    FINGERPRINT = None


def create_type(value: int, name: str) -> AttributeType:
    data = Convert.uint16data_from_value(value=value)
    fixed = AttributeType(data=data, value=data.value, endian=data.endian, name=name)
    AttributeType.cache(value=value, attribute_type=fixed)
    return fixed


# Comprehension-required range (0x0000-0x7FFF)
# Comprehension-optional range (0x8000-0xFFFF)

# [RFC-3489]
AttributeType.MAPPED_ADDRESS = create_type(value=0x0001, name='MAPPED-ADDRESS')
AttributeType.RESPONSE_ADDRESS = create_type(value=0x0002, name='RESPONSE-ADDRESS')
AttributeType.CHANGE_REQUEST = create_type(value=0x0003, name='CHANGE-REQUEST')
AttributeType.SOURCE_ADDRESS = create_type(value=0x0004, name='SOURCE-ADDRESS')
AttributeType.CHANGED_ADDRESS = create_type(value=0x0005, name='CHANGED-ADDRESS')
AttributeType.USERNAME = create_type(value=0x0006, name='USERNAME')
AttributeType.PASSWORD = create_type(value=0x0007, name='PASSWORD')
AttributeType.MESSAGE_INTEGRITY = create_type(value=0x0008, name='MESSAGE-INTEGRITY')
AttributeType.ERROR_CODE = create_type(value=0x0009, name='ERROR-CODE')
AttributeType.UNKNOWN_ATTRIBUTES = create_type(value=0x000A, name='UNKNOWN-ATTRIBUTES')
AttributeType.REFLECTED_FROM = create_type(value=0x000B, name='REFLECTED-FROM')

# [RFC-5389]
AttributeType.REALM = create_type(value=0x0014, name='REALM')
AttributeType.NONCE = create_type(value=0x0015, name='NONCE')
AttributeType.XOR_MAPPED_ADDRESS = create_type(value=0x0020, name='XOR-MAPPED-ADDRESS(0020)')

AttributeType.XOR_MAPPED_ADDRESS2 = create_type(value=0x8020, name='XOR-MAPPED-ADDRESS(8020)')
AttributeType.XOR_ONLY = create_type(value=0x8021, name='XOR-ONLY')
AttributeType.SOFTWARE = create_type(value=0x8022, name='SOFTWARE')
AttributeType.ALTERNATE_SERVER = create_type(value=0x8023, name='ALTERNATE-SERVER')
AttributeType.FINGERPRINT = create_type(value=0x8028, name='FINGERPRINT')


#
#  Attribute Length
#
AttributeLength = Length16

#
#  Attribute Value
#
AttributeValue = Value


class Attribute(Triad[AttributeType, AttributeLength, AttributeValue]):

    @classmethod
    def new(cls, tag: AttributeType,
            length: Optional[AttributeLength] = None,
            value: AttributeValue = RawValue.ZERO):
        if length is None:
            length = AttributeLength.new(value=value.size)
        data = tag.concat(length).concat(value)
        return cls(data=data, tag=tag, length=length, value=value)

    # TLV parser
    parser = None

    @classmethod
    def parse_attributes(cls, data: ByteArray):  # -> List[Attribute]
        return cls.parser.parse_entries(data=data)


class AttributeParser(TriadParser[Attribute, AttributeType, AttributeLength, AttributeValue],
                      TagParser[AttributeType],
                      LengthParser[AttributeType, AttributeLength],
                      ValueParser[AttributeType, AttributeLength, AttributeValue]):
    @property
    def tag_parser(self) -> TagParser[AttributeType]:
        return self

    @property
    def length_parser(self) -> LengthParser[AttributeType, AttributeLength]:
        return self

    @property
    def value_parser(self) -> ValueParser[AttributeType, AttributeLength, AttributeValue]:
        return self

    def create_entry(self, data: ByteArray,
                     tag: AttributeType, length: AttributeLength, value: AttributeValue) -> Attribute:
        return Attribute(data=data, tag=tag, length=length, value=value)

    # TagParser
    def parse_tag(self, data: ByteArray) -> Optional[AttributeType]:
        return AttributeType.parse(data=data)

    # LengthParser
    def parse_length(self, data: ByteArray, tag: AttributeType) -> Optional[AttributeLength]:
        return AttributeLength.parse(data=data, tag=tag)

    # ValueParser
    def parse_value(self, data: ByteArray, tag: AttributeType, length: AttributeLength) -> Optional[AttributeValue]:
        parser = self.__value_parsers.get(tag.name)
        if parser is None:
            return RawValue.parse(data=data, tag=tag, length=length)
        else:
            return parser.parse_value(data=data, tag=tag, length=length)

    __value_parsers: Dict[str, ValueParser] = {}  # type => parser

    @classmethod
    def register(cls, tag: AttributeType, parser: ValueParser):
        if parser is None:
            cls.__value_parsers.pop(tag.name, None)
        else:
            cls.__value_parsers[tag.name] = parser


Attribute.parser = AttributeParser()
