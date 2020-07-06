# -*- coding: utf-8 -*-
#
#   TLV: Tag Length Value
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

from .utils import int_to_bytes
from .data import Data
from .integer import IntegerData


"""
       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |         Type                  |            Length             |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Value (variable)                ....
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""


class Tag(Data):

    @classmethod
    def parse(cls, data: Data):
        if data.length < 2:
            return None
        elif data.length > 2:
            data = data.slice(end=2)
        return cls(data=data)


class Length(IntegerData):

    def __init__(self, data: Union[IntegerData, Data, bytes, bytearray]=None, value: int=None):
        if data is None:
            assert isinstance(value, int), 'value error: %s' % value
            data = int_to_bytes(value=value, length=2)
            super().__init__(data=data, value=value)
        elif isinstance(data, IntegerData):
            super().__init__(data=data)
        else:
            # bytes, bytearray or Data?
            super().__init__(data=data, value=value)

    # noinspection PyUnusedLocal
    @classmethod
    def parse(cls, data: Data, tag: Tag):
        if data.length < 2:
            return None
        elif data.length > 2:
            data = data.slice(end=2)
        value = data.get_uint16_value()
        return cls(data=data, value=value)


class Value(Data):

    @classmethod
    def parse(cls, data: Data, tag: Tag, length: Length=None):  # -> Value:
        if data is None or data.length == 0:
            return None
        elif cls is Value:
            # get attribute parser with type
            assert isinstance(tag, Value), 'attribute type error: %s' % tag
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
    def register(cls, tag: Tag, value_class):
        if value_class is None:
            cls.__value_classes.pop(tag)
        elif issubclass(value_class, Value):
            cls.__value_classes[tag] = value_class
        else:
            raise TypeError('%s must be subclass of AttributeValue' % value_class)


class TagLengthValue(Data):

    def __init__(self, data=None, tag: Tag=None, length: Length=None, value: Value=None):
        """
        Initialize with another TLV object
        Initialize with Data and Tag + Value
        Initialize with Tag + Length + Value

        :param data:   bytes, bytearray, Data, another TLV object or None
        :param tag:
        :param length:
        :param value:
        """
        if data is None:
            # building data with Tag + Length + Value
            assert tag is not None, 'TLV tag should not be empty'
            data = tag
            if length is not None:
                data = data.concat(length)
            if value is not None:
                data = data.concat(value)
        elif isinstance(data, TagLengthValue):
            # get Tag + Value from another TLV object
            tag = data.tag
            value = data.value
        super().__init__(data=data)
        self.__tag = tag
        self.__value = value

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '/* %s */ %s: "%s"' % (clazz, self.tag, self.value)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '/* %s */ %s: "%s"' % (clazz, self.tag, self.value)

    @property
    def tag(self) -> Tag:
        return self.__tag

    @property
    def value(self) -> Optional[Value]:
        return self.__value

    @classmethod
    def parse_all(cls, data: Data) -> list:
        array = []
        remaining = data.length
        while remaining > 0:
            item = cls.parse(data=data)
            if item is None:
                # data error
                break
            array.append(item)
            # next item
            pos = item.length
            data = data.slice(start=pos)
            remaining -= pos
        return array

    @classmethod
    def parse(cls, data: Data):  # -> TagLengthValue:
        # get tag
        tag = cls.parse_tag(data=data)
        if tag is None:
            return None
        offset = tag.length
        assert offset <= data.length, 'data length error: %d, offset: %d' % (data.length, offset)
        # get length
        length = cls.parse_length(data=data.slice(start=offset), tag=tag)
        if length is None:
            # get value with unlimited length
            value = cls.parse_value(data=data.slice(start=offset), tag=tag)
        else:
            # get value with limited length
            offset += length.length
            end = offset + length.value
            if end < offset or end > data.length:
                raise IndexError('data length error: %d, %d' % (length.value, data.length))
            value = cls.parse_value(data=data.slice(start=offset, end=end), tag=tag, length=length)
        if value is not None:
            offset += value.length
        # check length
        if offset > data.length:
            raise AssertionError('TLV length error: %d, %d' % (offset, data.length))
        elif offset < data.length:
            data = data.slice(end=offset)
        return cls._create(data=data, tag=tag, value=value)

    @classmethod
    def parse_tag(cls, data: Data) -> Optional[Tag]:
        # TODO: override for user-defined Tag
        return Tag.parse(data=data)

    @classmethod
    def parse_length(cls, data: Data, tag: Tag) -> Optional[Length]:
        # TODO: override for user-defined Length
        return Length.parse(data=data, tag=tag)

    @classmethod
    def parse_value(cls, data: Data, tag: Tag, length: Length=None) -> Optional[Value]:
        # TODO: override for user-defined Value
        return Value.parse(data=data, tag=tag, length=length)

    @classmethod
    def _create(cls, data: Data, tag: Tag, value: Value=None):
        # TODO: override for user-defined TLV
        return cls(data=data, tag=tag, value=value)
