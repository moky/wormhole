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
"""

import threading
from typing import Union, Optional

from udp.ba import ByteArray, Data, MutableData
from udp.ba import Endian, UInt16Data, Convert


"""
                        0                 1
                        2  3  4 5 6 7 8 9 0 1 2 3 4 5

                       +--+--+-+-+-+-+-+-+-+-+-+-+-+-+
                       |M |M |M|M|M|C|M|M|M|C|M|M|M|M|
                       |11|10|9|8|7|1|6|5|4|0|3|2|1|0|
                       +--+--+-+-+-+-+-+-+-+-+-+-+-+-+

                Figure 3: Format of STUN Message Type Field
"""


class MessageType(UInt16Data):

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
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Optional[MessageType]:
        if isinstance(data, cls):
            return data
        elif not isinstance(data, UInt16Data):
            data = Convert.uint16data_from_data(data=data)
        if data is None or data.value > 0x3FFF:
            # format: 00xx xxxx, xxxx xxxx
            return None
        fixed = cls.__message_types.get(data.value)
        if fixed is None:
            # name = 'MessageType-0x%04X' % ui16.value
            # fixed = cls(data=ui16, value=ui16.value, name=name)
            raise LookupError('msg type error: %d' % data.value)
        return fixed

    @classmethod
    def cache(cls, value: int, msg_type):
        cls.__message_types[value] = msg_type

    __message_types = {}  # int -> MessageType

    # fixed types for a STUN message
    BIND_REQUEST = None
    BIND_RESPONSE = None
    BIND_ERROR_RESPONSE = None
    SHARED_SECRET_REQUEST = None
    SHARED_SECRET_RESPONSE = None
    SHARED_SECRET_ERROR_RESPONSE = None


def create_type(value: int, name: str) -> MessageType:
    data = Convert.uint16data_from_value(value=value)
    fixed = MessageType(data=data, value=value, endian=data.endian, name=name)
    MessageType.cache(value=value, msg_type=fixed)
    return fixed


MessageType.BIND_REQUEST = create_type(value=0x0001, name='Binding Request')
MessageType.BIND_RESPONSE = create_type(value=0x0101, name='Binding Response')
MessageType.BIND_ERROR_RESPONSE = create_type(value=0x0111, name='Binding Error Response')
MessageType.SHARED_SECRET_REQUEST = create_type(value=0x0002, name='Shared Secret Request')
MessageType.SHARED_SECRET_RESPONSE = create_type(value=0x0102, name='Shared Secret Response')
MessageType.SHARED_SECRET_ERROR_RESPONSE = create_type(value=0x0112, name='Shared Secret Error Response')


class TransactionID(Data):

    # Magic Cookie
    MagicCookie = Convert.uint32data_from_value(value=0x2112A442)

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

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Optional[TransactionID]:
        if isinstance(data, cls):
            return data
        if isinstance(data, ByteArray):
            if data.size < 16:
                return None
            elif data.size > 16:
                data = data.slice(start=0, end=16)
        else:
            data_size = len(data)
            if data_size < 16:
                return None
            elif data_size > 16:
                data = data[0:16]
        return cls(data=data)

    __number_lock = threading.Lock()
    __number_hi = Convert.int32_from_data(data=Data.random(size=4))
    __number_mi = Convert.int32_from_data(data=Data.random(size=4))
    __number_lo = Convert.int32_from_data(data=Data.random(size=4))

    @classmethod
    def generate(cls):  # -> TransactionID:
        with cls.__number_lock:
            if cls.__number_lo < 0xFFFFFFFF:
                cls.__number_lo += 1
            else:
                cls.__number_lo = 0
                if cls.__number_mi < 0xFFFFFFFF:
                    cls.__number_mi += 1
                else:
                    cls.__number_mi = 0
                    if cls.__number_hi < 0xFFFFFFFF:
                        cls.__number_hi += 1
                    else:
                        cls.__number_hi = 0
            hi = cls.__number_hi
            mi = cls.__number_mi
            lo = cls.__number_lo
        # convert integer values to Data
        hi = Convert.uint32data_from_value(value=hi)
        mi = Convert.uint32data_from_value(value=mi)
        lo = Convert.uint32data_from_value(value=lo)
        data = cls.MagicCookie.concat(hi).concat(mi).concat(lo)
        return cls(data=data)


"""
    STUN Message Structure
    ~~~~~~~~~~~~~~~~~~~~~~

   STUN messages are encoded in binary using network-oriented format
   (most significant byte or octet first, also commonly known as big-
   endian).  The transmission order is described in detail in Appendix B
   of RFC 791 [RFC0791].  Unless otherwise noted, numeric constants are
   in decimal (base 10).

   All STUN messages MUST start with a 20-byte header followed by zero
   or more Attributes.  The STUN header contains a STUN message type,
   magic cookie, transaction ID, and message length.
   
       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |0 0|     STUN Message Type     |         Message Length        |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                         Magic Cookie                          |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                                                                
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                            Transaction ID (96 bits)                   
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                                                      |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

                  Figure 2: Format of STUN Message Header

   The message length MUST contain the size, in bytes, of the message
   not including the 20-byte STUN header.  Since all STUN attributes are
   padded to a multiple of 4 bytes, the last 2 bits of this field are
   always zero.  This provides another way to distinguish STUN packets
   from packets of other protocols.
"""


class Header(Data):

    def __init__(self, data: Union[bytes, bytearray, ByteArray],
                 msg_type: MessageType, msg_length: int, trans_id: TransactionID):
        if isinstance(data, ByteArray):
            super().__init__(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            super().__init__(buffer=data)
        self.__msg_type = msg_type
        self.__msg_length = msg_length
        self.__trans_id = trans_id

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        mt = self.msg_type
        ml = self.msg_length
        return '<%s: %d, "%s" msg_len=%d />' % (clazz, self.size, mt, ml)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        mt = self.msg_type
        ml = self.msg_length
        return '<%s: %d, "%s" msg_len=%d />' % (clazz, self.size, mt, ml)

    @property
    def msg_type(self) -> MessageType:
        return self.__msg_type

    @property
    def msg_length(self) -> int:
        return self.__msg_length

    @property
    def trans_id(self) -> TransactionID:
        return self.__trans_id

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> Optional[Header]:
        if isinstance(data, cls):
            return data
        elif not isinstance(data, ByteArray):
            data = Data(buffer=data)
        # get message type
        msg_type = MessageType.parse(data=data)
        if msg_type is None:
            return None
        pos = msg_type.size
        # get message length
        msg_len = Convert.uint16data_from_data(data=data, start=pos)
        if msg_len is None:
            return None
        pos += msg_len.size
        # get transaction ID
        trans_id = TransactionID.parse(data=data.slice(start=pos))
        if trans_id is None:
            return None
        pos += trans_id.size
        assert pos == 20, 'header length error: %d' % pos
        if data.size > pos:
            data = data.slice(start=0, end=pos)
        # create
        assert msg_len.value & 0x0003 == 0, 'msg length error: %d' % msg_len.value
        return cls(data=data, msg_type=msg_type, msg_length=msg_len.value, trans_id=trans_id)

    @classmethod
    def new(cls, msg_type: MessageType, msg_length: int, trans_id: Optional[TransactionID] = None):  # -> Header:
        assert msg_length & 0x0003 == 0, 'msg length error: %d' % msg_length
        msg_len = Convert.uint16data_from_value(value=msg_length)
        if trans_id is None:
            trans_id = TransactionID.generate()
        # concat(msg_type, msg_len, trans_id)
        size = msg_type.size + msg_len.size + trans_id.size
        data = MutableData(capacity=size)
        data.append(msg_type)
        data.append(msg_len)
        data.append(trans_id)
        return cls(data=data, msg_type=msg_type, msg_length=msg_length, trans_id=trans_id)
