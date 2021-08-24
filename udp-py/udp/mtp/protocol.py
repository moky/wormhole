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
from typing import Union

from ..ba import ByteArray, Data, Convert, UInt8Data

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


class DataType(UInt8Data):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], value: int, name: str):
        super().__init__(data=data, value=value)
        self.__name = name

    def __str__(self) -> str:
        return self.__name

    def __repr__(self) -> str:
        return self.__name

    @property
    def name(self) -> str:
        return self.__name

    @property
    def is_response(self) -> bool:
        return (self.value & 0x01) != 0

    @property
    def is_fragment(self) -> bool:
        return (self.value & 0x08) != 0

    @property
    def is_command(self) -> bool:
        return (self.value & 0x0F) == 0x00

    @property
    def is_command_response(self) -> bool:
        return (self.value & 0x0F) == 0x01

    @property
    def is_message(self) -> bool:
        return (self.value & 0x0F) == 0x02

    @property
    def is_message_response(self) -> bool:
        return (self.value & 0x0F) == 0x03

    @property
    def is_message_fragment(self) -> bool:
        return (self.value & 0x0F) == 0x0A

    #
    #   Factories
    #

    @classmethod
    def from_data(cls, data: Union[bytes, bytearray, ByteArray]):
        if not isinstance(data, UInt8Data):
            data = UInt8Data.from_data(data=data)
        if data is not None:
            return cls.__get(data=data)

    @classmethod
    def from_int(cls, value: int):
        data = UInt8Data.from_int(value=value)
        return cls.__get(data=data)

    @classmethod
    def __get(cls, data: UInt8Data):
        value = data.value & 0x0F
        fixed = cls.__data_types.get(value)
        if fixed is not None:
            # assert isinstance(fixed, DataType)
            return cls(data=data, value=value, name=fixed.name)

    @classmethod
    def cache(cls, value: int, data_type):
        cls.__data_types[value] = data_type

    __data_types = {}  # int -> DataType

    # fixed types
    COMMAND = None
    COMMAND_RESPONSE = None
    MESSAGE = None
    MESSAGE_RESPONSE = None
    MESSAGE_FRAGMENT = None


def create_type(value: int, name: str) -> DataType:
    data = UInt8Data.from_int(value=value)
    fixed = DataType(data=data, value=value, name=name)
    DataType.cache(value=value, data_type=fixed)
    return fixed


DataType.COMMAND = create_type(value=0x00, name='Command')
DataType.COMMAND_RESPONSE = create_type(value=0x01, name='Command Response')
DataType.MESSAGE = create_type(value=0x02, name='Message')
DataType.MESSAGE_RESPONSE = create_type(value=0x03, name='Message Response')
DataType.MESSAGE_FRAGMENT = create_type(value=0x0A, name='Message Fragment')


class TransactionID(Data):

    ZERO = None  # TransactionID(data=Data(b'\0\0\0\0\0\0\0\0'))

    def __init__(self, data: Union[bytes, bytearray, ByteArray]):
        if isinstance(data, ByteArray):
            super().__init__(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            super().__init__(buffer=data)

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: %s />' % (clazz, self.get_bytes())

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: %s />' % (clazz, self.get_bytes())

    #
    #   Factories
    #

    @classmethod
    def from_data(cls, data: Union[bytes, bytearray, ByteArray]):  # -> TransactionID
        if isinstance(data, cls):
            return data
        if isinstance(data, ByteArray):
            if data.size < 8:
                return None
            elif data.size > 8:
                data = data.slice(start=0, end=8)
        else:
            data_size = len(data)
            if data_size < 8:
                return None
            elif data_size > 8:
                data = data[:8]
        return cls(data=data)

    __number_lock = threading.Lock()
    __number_high = Convert.int32_from_data(data=Data.random(size=4))
    __number_low = Convert.int32_from_data(data=Data.random(size=4))

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
            hi = Convert.uint32data_from_value(value=cls.__number_high)
            lo = Convert.uint32data_from_value(value=cls.__number_low)
        return cls(data=hi.concat(lo))


TransactionID.ZERO = TransactionID(data=Data(b'\0\0\0\0\0\0\0\0'))
