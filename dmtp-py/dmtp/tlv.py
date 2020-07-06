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

from udp.tlv import Data, MutableData, VarIntData
from udp.tlv import Tag, Length, Value, TagLengthValue


class FieldName(Tag):

    def __init__(self, data=None, name: str=None):
        if data is None:
            assert name is not None, 'field name should not be empty'
            data = name.encode('utf-8')
            mutable = MutableData(capacity=len(data) + 1)
            mutable.append(data)
            mutable.append(0)  # add '\0' for tail
            data = mutable
        elif name is None:
            name = str(data).rstrip()
        super().__init__(data=data)
        self.__name = name

    def __eq__(self, other) -> bool:
        if isinstance(other, FieldName):
            return self.__name == other.__name
        if isinstance(other, str):
            return self.__name == other
        return super().__eq__(other=other)

    def __hash__(self) -> int:
        return hash(self.__name)

    def __str__(self):
        return self.__name

    def __repr__(self):
        return self.__name

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def parse(cls, data: Data):
        pos = data.find(b'\0')
        if pos < 0:
            return None
        if pos < data.length:
            data = data.slice(end=pos+1)  # includes the tail '\0'
        name = data.get_bytes(end=pos).decode('utf-8')
        return cls(name=name, data=data)


class FieldLength(VarIntData, Length):

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Data, tag: FieldName):
        value = VarIntData(data=data)
        return cls(data=data)


class FieldValue(Value):

    @classmethod
    def parse(cls, data: Data, tag: FieldName, length: FieldLength=None):  # -> FieldValue:
        if data is None or data.length == 0:
            return None
        elif cls is FieldValue:
            # get field parser with type
            clazz = cls.__value_classes.get(tag)
            if clazz is not None:
                # create instance by subclass
                return clazz.parse(data=data, tag=tag, length=length)
        return cls(data=data)

    #
    #   Runtime
    #
    __value_classes = {}  # tag -> class

    @classmethod
    def register(cls, tag: FieldName, value_class):
        if value_class is None:
            cls.__value_classes.pop(tag)
        elif issubclass(value_class, FieldValue):
            cls.__value_classes[tag] = value_class
        else:
            raise TypeError('%s must be subclass of FieldValue' % value_class)


class Field(TagLengthValue):

    def __init__(self, data=None, tag: FieldName=None, length: FieldLength=None, value: FieldValue=None):
        if data is None and length is None:
            if value is None:
                length = FieldLength(value=0)
            else:
                length = FieldLength(value=value.length)
        super().__init__(data=data, tag=tag, length=length, value=value)

    @classmethod
    def parse_tag(cls, data: Data) -> Optional[FieldName]:
        return FieldName.parse(data=data)

    @classmethod
    def parse_length(cls, data: Data, tag: FieldName) -> Optional[FieldLength]:
        return FieldLength.parse(data=data, tag=tag)

    @classmethod
    def parse_value(cls, data: Data, tag: FieldName, length: Length = None) -> Optional[FieldValue]:
        return FieldValue.parse(data=data, tag=tag, length=length)

    # field names
    ID = FieldName(name='ID')                            # user ID
    SOURCE_ADDRESS = FieldName(name='SOURCE-ADDRESS')    # source-address (local IP and port)
    MAPPED_ADDRESS = FieldName(name='MAPPED-ADDRESS')    # mapped-address (public IP and port)
    RELAYED_ADDRESS = FieldName(name='RELAYED-ADDRESS')  # relayed-address (server IP and port)
    TIME = FieldName(name='TIME')                        # timestamp (uint32) stored in network order (big endian)
    SIGNATURE = FieldName(name='SIGNATURE')              # verify with ('ADDR' + 'TIME') and meta.key
    NAT = FieldName(name='NAT')                          # NAT type
