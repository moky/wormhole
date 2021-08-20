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

from abc import abstractmethod
from typing import TypeVar, Generic, Union, Optional

from udp.ba import ByteArray, Data
from udp.ba import IntegerData, UInt8Data, UInt16Data, UInt32Data, VarIntData, Convert


"""
       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |         Type                  |            Length             |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Value (variable)                ....
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""


class Tag(ByteArray):
    """ TLV Tag/Type """
    pass


T = TypeVar('T')  # Type


class TagParser(Generic[T]):
    """ Tag Parser """

    @abstractmethod
    def parse_tag(self, data: ByteArray) -> Optional[T]:
        """ Parse Tag from data """
        raise NotImplemented


"""
    Tags
    ~~~~
"""


class Tag8(UInt8Data, Tag):
    """ Fixed size Tag (8 bits) """

    ZERO = None  # Tag8.parse(data=UInt8Data.ZERO)

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Tag8
        """ parse Tag """
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt8Data):
            data = UInt8Data.from_data(data=data)
        if data is not None:
            return cls(data=data, value=data.value)

    @classmethod
    def new(cls, value: int):  # -> Tag8
        data = UInt8Data.from_int(value=value)
        return cls(data=data, value=data.value)


class Tag16(UInt16Data, Tag):
    """ Fixed size Tag (16 bits) """

    ZERO = None  # Tag16.parse(data=UInt16Data.ZERO)

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Tag16
        """ parse Tag """
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt16Data):
            data = Convert.uint16data_from_data(data=data)
        if data is not None:
            return cls(data=data, value=data.value, endian=data.endian)

    @classmethod
    def new(cls, value: int):  # -> Tag16
        data = Convert.uint16data_from_value(value=value)
        return cls(data=data, value=data.value, endian=data.endian)


class Tag32(UInt32Data, Tag):
    """ Fixed size Tag (32 bits) """

    ZERO = None  # Tag32.from_data(data=UInt32Data.ZERO)

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Tag32
        """ parse Tag """
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt32Data):
            data = Convert.uint32data_from_data(data=data)
        if data is not None:
            return cls(data=data, value=data.value, endian=data.endian)

    @classmethod
    def new(cls, value: int):  # -> Tag32
        data = Convert.uint32data_from_value(value=value)
        return cls(data=data, value=data.value, endian=data.endian)


Tag8.ZERO = Tag8.parse(data=UInt8Data.ZERO)
Tag16.ZERO = Tag16.parse(data=UInt16Data.ZERO)
Tag32.ZERO = Tag32.parse(data=UInt32Data.ZERO)


"""
    Variable size Tag
    ~~~~~~~~~~~~~~~~~
    A tag that starts with a variable integer indicating its content length
    
         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |     Length    |               Content (variable)              |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""


class VarTag(Data, Tag):

    ZERO = None  # VarTag.new(content=Data.ZERO)

    def __init__(self, data: Union[bytes, bytearray, ByteArray], length: IntegerData, content: ByteArray):
        if isinstance(data, ByteArray):
            super().__init__(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            super().__init__(buffer=data)
        self.__length = length
        self.__content = content

    @property
    def length(self) -> IntegerData:
        return self.__length

    @property
    def content(self) -> ByteArray:
        return self.__content

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> VarTag
        """ parse Tag """
        if isinstance(data, cls):
            return data
        # get length
        length = VarIntData.from_data(data=data)
        if length is None:
            return None
        start = length.size
        end = start + length.value
        if end > data.size:
            # raise ValueError('VarTag length error: %d, %d, %d' % (start, end, data.size))
            return None
        elif end < data.size:
            # cut the tail
            data = data.slice(start=0, end=end)
        # get content
        content = data.slice(start=start, end=end)
        return cls(length=length, content=content, data=data)

    @classmethod
    def new(cls, content: ByteArray, length: Optional[VarIntData] = None):  # -> VarTag
        if length is None:
            length = VarIntData.from_int(value=content.size)
        data = length.concat(content)
        return cls(data=data, length=length, content=content)


VarTag.ZERO = VarTag.new(content=Data.ZERO)
