# -*- coding: utf-8 -*-
#
#   MTP: Message Transfer Protocol
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
    Protocol
    ~~~~~~~~

    Data format in UDP payload
"""

import threading

from .tlv.utils import random_bytes, bytes_to_int
from .tlv import Data, UInt32Data

"""
    Data Type:
    
          0   1   2   3   4   5   6   7
        +---+---+---+---+---+---+---+---+
        |               | F |   | M | A |
        |               | R |   | S | C |
        |               | G |   | G | K |
        +---+---+---+---+---+---+---+---+
    
        Command                  : 0x00 (0000 0000)
        Command Respond          : 0x01 (0000 0001)
        Message                  : 0x02 (0000 0010)
        Message Respond          : 0x03 (0000 0011)
        Message Fragment         : 0x0A (0000 1010)
"""


class DataType:

    def __init__(self, value: int, name: str):
        super().__init__()
        self.__value = value
        self.__name = name
        self.__data_types[value] = self

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if isinstance(other, DataType):
            return self.__value == other.__value
        if isinstance(other, int):
            return self.__value == other

    def __hash__(self) -> int:
        return hash(self.__value)

    def __str__(self) -> str:
        return self.__name

    def __repr__(self) -> str:
        return self.__name

    @property
    def value(self) -> int:
        return self.__value

    __data_types = {}  # int -> DataType

    @classmethod
    def new(cls, value: int):
        t = cls.__data_types.get(value)
        if t is None:
            # name = 'DataType-%d' % value
            # t = cls(value=value, name=name)
            # raise LookupError('data type error: %d' % value)
            return None
        return t


# data types
Command = DataType(0, name='Command')
CommandRespond = DataType(1, name='Command Respond')
Message = DataType(2, name='Message')
MessageRespond = DataType(3, name='Message Respond')
MessageFragment = DataType(10, name='Message Fragment')


class TransactionID(Data):

    ZERO = None  # TransactionID(data=Data(b'\0\0\0\0\0\0\0\0'))

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: %s />' % (clazz, self.get_bytes())

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: %s />' % (clazz, self.get_bytes())

    @classmethod
    def parse(cls, data: Data):  # -> TransactionID
        if data.length < 8:
            # raise ValueError('transaction ID length error: %d' % data.length)
            return None
        elif data.length > 8:
            data = data.slice(end=8)
        return cls(data=data)

    __number_lock = threading.Lock()
    __number_high = bytes_to_int(random_bytes(4))
    __number_low = bytes_to_int(random_bytes(4))

    @classmethod
    def generate(cls):  # -> TransactionID:
        with cls.__number_lock:
            if cls.__number_low < 0xFFFFFFFF:
                cls.__number_low += 1
            else:
                cls.__number_low = 0
                if cls.__number_high < 0xFFFFFFFF:
                    cls.__number_high += 1
                else:
                    cls.__number_high = 0
            hi = UInt32Data(value=cls.__number_high)
            lo = UInt32Data(value=cls.__number_low)
        return TransactionID(data=hi.concat(lo))


TransactionID.ZERO = TransactionID(data=Data(b'\0\0\0\0\0\0\0\0'))
