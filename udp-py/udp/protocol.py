# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
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

"""
    Protocol
    ~~~~~~~~

    Data format
"""

from typing import Union

from .data import Data, UInt8Data
from .data import random_bytes, bytes_to_int, uint32_to_bytes

"""
    Data Type:
    
          0   1   2   3   4   5   6   7
        +---+---+---+---+---+---+---+---+
        |   |   |   | F |   |   | M | A |
        |   |   |   | R |   |   | S | C |
        |   |   |   | G |   |   | G | K |
        +---+---+---+---+---+---+---+---+
"""


class DataType(UInt8Data):

    def __init__(self, value: int, data: bytes=None, name: str='Unknown Type'):
        super().__init__(value=value, data=data)
        self.__name = name
        s_data_types[value] = self

    def __str__(self):
        clazz = self.__class__.__name__
        return '<%s: 0x%04X "%s" />' % (clazz, self.value, self.__name)

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 1:
            return None
        elif data_len > 1:
            data = data[:1]
        value = bytes_to_int(data=data)
        t = s_data_types.get(value)
        if t is None:
            return cls(value=value, data=data)
        else:
            return t


# data types
s_data_types = {}
Command = DataType(0x00, name='Command')
CommandRespond = DataType(0x01, name='Command Respond')
Message = DataType(0x02, name='Message')
MessageRespond = DataType(0x03, name='Message Respond')
MessageFragment = DataType(0x12, name='Message Fragment')
MessageFragmentRespond = DataType(0x13, name='Message Fragment Respond')


class SequenceNumber(Data):

    __sequence_number = bytes_to_int(data=random_bytes(4))

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 4:
            return None
        elif data_len > 4:
            data = data[:4]
        return cls(data=data)

    @classmethod
    def new(cls):
        # create self-increasing number
        sn = (cls.__sequence_number + 1) & 0xFFFFFFFF
        cls.__sequence_number = sn
        data = uint32_to_bytes(sn)
        return cls(data=data)


"""
    Package Header:
    
         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'W'      |      'H'      |    Version    |   Data Type   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                   Sequence Number (32 bits)                   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  Optional: Fragment count(varint), offset(varint)
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      
        If data type is a fragment message (or respond), there is a varint
        'count' following the sequence number, which indicates the message
        was split to how many fragments; and there is another varint 'offset'
        following the 'count'; after them is the message fragment.
"""


class Header:

    def __init__(self, data: bytes, data_type: DataType, sn: SequenceNumber, version: int=0):
        super().__init__()
        self.__data = data
        self.__type = data_type
        self.__sn = sn
        self.__version = version

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def data_type(self) -> DataType:
        return self.__type

    @property
    def sequence_number(self) -> SequenceNumber:
        return self.__sn

    @property
    def version(self) -> int:
        return self.__version

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 8 or data[0] != 'W' or data[1] != 'H':
            return None
        version = data[2]
        prefix = data[:3]
        data = data[3:]
        # get data type
        _type = DataType.parse(data=data)
        if _type is None:
            return None
        else:
            data = data[_type.length:]
        # get sequence number
        _sn = SequenceNumber.parse(data=data)
        if _sn is None:
            return None
        # build data
        data = prefix + _type.data + _sn.data
        return cls(data=data, data_type=_type, sn=_sn, version=version)

    @classmethod
    def new(cls, data_type: DataType, sn: SequenceNumber=None):
        if sn is None:
            # generate sequence number
            sn = SequenceNumber.new()
        # build data
        data = b'WH\0' + data_type.data + sn.data
        return Header(data=data, data_type=data_type, sn=sn)


class Package:

    MAX_LEN = 512  # max package body length

    def __init__(self, data: bytes, head: Header, body: bytes):
        super().__init__()
        self.__data = data
        self.__head = head
        self.__body = body

    @property
    def data(self) -> bytes:
        if self.__data is None:
            head = self.head.data
            body = self.body
            self.__data = head + body
        return self.__data

    @property
    def head(self) -> Header:
        return self.__head

    @property
    def body(self) -> bytes:
        return self.__body

    @classmethod
    def parse(cls, data: bytes):
        # get package head
        head = Header.parse(data=data)
        if head is None:
            # package head error
            return None
        head_len = len(head.data)
        # get package body
        body = data[head_len:]
        return Package(data=data, head=head, body=body)

    @classmethod
    def new(cls, data_type: DataType, sn: SequenceNumber=None, body: bytes=b'') -> Union[object, list]:
        if sn is None:
            # generate sequence number
            sn = SequenceNumber.new()
        body_len = len(body)
        if body_len > cls.MAX_LEN:
            assert data_type == Message or data_type == MessageRespond, 'body too long: %d, %s' % (body_len, data_type)
            # TODO: split package
        else:
            head = Header.new(data_type=data_type, sn=sn)
            data = head.data + body
            return Package(data=data, head=head, body=body)
