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

from udp.tlv.data import base64_encode
from udp.tlv.data import bytes_to_varint, varint_to_bytes, uint8_to_bytes, uint32_to_bytes
from udp.tlv import Data, VarIntData, UInt8Data, UInt32Data
from udp.tlv import Tag, Length, Value, TagLengthValue


class VarName(Tag):

    def __init__(self, name: str, data: bytes = None):
        if data is None:
            data = name.encode('utf-8') + b'\0'
        super().__init__(data=data)
        self.__name = name

    def __eq__(self, other) -> bool:
        if isinstance(other, Data):
            return self.data == other.data
        if isinstance(other, bytes):
            return self.data == other
        if isinstance(other, str):
            return self.name == other

    def __hash__(self) -> int:
        return hash(self.__name)

    def __str__(self):
        return '"%s"' % self.__name

    def __repr__(self):
        return '"%s"' % self.__name

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def parse(cls, data: bytes):
        pos = data.find(b'\0')
        if pos < 1:
            return None
        data = data[:pos + 1]
        name = data.rstrip(b'\0').decode('utf-8')
        return cls(name=name, data=data)


class VarLength(VarIntData, Length):

    def __init__(self, value: int, data: bytes = None):
        if data is None:
            data = varint_to_bytes(value)
        super().__init__(data=data, value=value)

    def __str__(self):
        return '%d' % self.__value

    def __repr__(self):
        return '%d' % self.__value

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: bytes, tag: Tag):
        value, length = bytes_to_varint(data=data)
        return cls(data=data[:length], value=value)


class Field(TagLengthValue):

    def __init__(self, tag: Tag, value: Value=None, data: bytes = None):
        if data is None:
            if value is None:
                data = tag.data + varint_to_bytes(0)
            else:
                data = tag.data + varint_to_bytes(len(value.data)) + value.data
        super().__init__(data=data, tag=tag, value=value)

    def __str__(self):
        clazz = self.__class__.__name__
        return '/* %s */ %s: %s' % (clazz, self.tag, self.value)

    def __repr__(self):
        clazz = self.__class__.__name__
        return '/* %s */ %s: %s' % (clazz, self.tag, self.value)

    @classmethod
    def parse_tag(cls, data: bytes) -> Optional[VarName]:
        return VarName.parse(data=data)

    @classmethod
    def parse_length(cls, data: bytes, tag: Tag) -> Optional[VarLength]:
        return VarLength.parse(data=data, tag=tag)

    @classmethod
    def parse_value(cls, data: bytes, tag: Tag, length: Length = None) -> Optional[Value]:
        if length is not None:
            # check length
            data_len = len(data)
            if data_len > length.value:
                data = data[:length.value]
            else:
                assert data_len == length.value, 'data length not enough: %d < %d' % (data_len, length.value)
        # get attribute parser with type
        parser = s_value_parsers.get(tag)
        if parser is None:
            parser = Value
        return parser.parse(data=data, tag=tag, length=length)


# classes for parsing value
s_value_parsers = {}


class FieldsValue(Value):

    def __init__(self, fields: list, data: bytes = None):
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

    def __str__(self):
        return '%s' % self.to_dict()

    def __repr__(self):
        return '%s' % self.to_dict()

    @property
    def fields(self) -> list:
        return self.__fields

    def _set_field(self, field: Field):
        pass

    @classmethod
    def parse(cls, data: bytes, tag: Tag, length: Length = None):
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

    def to_dict(self) -> dict:
        dictionary = {}
        array = self.__fields
        for item in array:
            assert isinstance(item, Field), 'field item error: %s' % item
            name = item.tag
            value = item.value
            if isinstance(value, FieldsValue):
                value = value.to_dict()
            same = dictionary.get(name)
            if same is None:
                dictionary[name] = value
            elif isinstance(same, list):
                # add value to the array with the same name
                same.append(value)
            else:
                # convert values with the same name to an array
                dictionary[name] = [same, value]
        return dictionary


class BinaryValue(Value):

    def __init__(self, data: bytes):
        super().__init__(data=data)

    def __str__(self):
        return '"%s"' % base64_encode(self.data)

    def __repr__(self):
        return '"%s"' % base64_encode(self.data)


class ByteValue(UInt8Data, Value):

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = uint8_to_bytes(value=value)
        super().__init__(data=data, value=value)

    def __str__(self):
        return '%d' % self.value

    def __repr__(self):
        return '%d' % self.value

    @classmethod
    def parse(cls, data: bytes, tag: Tag, length: Length=None):
        return super().from_bytes(data=data)


class TimestampValue(UInt32Data, Value):

    def __init__(self, value: int, data: bytes=None):
        if data is None:
            data = uint32_to_bytes(value=value)
        super().__init__(data=data, value=value)

    def __str__(self):
        return '%d' % self.value

    def __repr__(self):
        return '%d' % self.value

    @classmethod
    def parse(cls, data: bytes, tag: Tag, length: Length=None):
        return super().from_bytes(data=data)


class StringValue(Value):

    def __init__(self, string: str, data: bytes=None):
        if data is None:
            data = string.encode('utf-8')
        super().__init__(data=data)
        self.__string = string

    def __str__(self):
        return '"%s"' % self.__string

    def __repr__(self):
        return '"%s"' % self.__string

    @property
    def string(self) -> str:
        return self.__string

    @classmethod
    def parse(cls, data: bytes, tag: Tag, length: Length=None):
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
        return cls(string=data.decode('utf-8'), data=data)
