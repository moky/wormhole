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

from ..tlv import Data
from ..tlv.data import random_bytes
from ..tlv.data import bytes_to_int, uint8_to_bytes, uint32_to_bytes

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

    def __init__(self, value: int, name: str='Unknown Type'):
        super().__init__()
        self.__value = value
        self.__name = name
        s_data_types[value] = self

    def __str__(self):
        clazz = self.__class__.__name__
        return '<%s: 0x%02X "%s" />' % (clazz, self.value, self.__name)

    @property
    def value(self) -> int:
        return self.__value

    @classmethod
    def new(cls, value: int):
        t = s_data_types.get(value)
        if t is None:
            t = cls(value=value)
        return t


# data types
s_data_types = {}
Command = DataType(0, name='Command')
CommandRespond = DataType(1, name='Command Respond')
Message = DataType(2, name='Message')
MessageRespond = DataType(3, name='Message Respond')
MessageFragment = DataType(10, name='Message Fragment')


class TransactionID(Data):

    def __str__(self):
        clazz = self.__class__.__name__
        return '<%s: %s />' % (clazz, self.data)

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 8:
            raise ValueError('transaction ID length error: %d' % data_len)
        elif data_len > 8:
            data = data[:8]
        return cls(data=data)

    __number_lock = threading.Lock()
    __number_high = bytes_to_int(random_bytes(4))
    __number_low = bytes_to_int(random_bytes(4))

    @classmethod
    def new(cls):
        with cls.__number_lock:
            if cls.__number_low < 0xFFFFFFFF:
                cls.__number_low += 1
            else:
                cls.__number_low = 0
                if cls.__number_high < 0xFFFFFFFF:
                    cls.__number_high += 1
                else:
                    cls.__number_high = 0
            data = uint32_to_bytes(cls.__number_high) + uint32_to_bytes(cls.__number_low)
        return cls(data=data)


"""
    Package Header:
    
         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'D'      |      'I'      |      'M'      | H-Len |  Type |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Transaction ID (64 bits)                    
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                             Transaction ID (64 bits)                   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |               Fragment Count (32 bits) OPTIONAL               |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |               Fragment Index (32 bits) OPTIONAL               |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        
        ** Magic Code **:
            Always be 'DIM'
            
        ** Header Length **:
            4 bits header length is the length of the header in 32 bit words.
            Note that the minimum value for a correct header is 3 (12 bytes).
            
        ** Data Type **:
            Indicates what kind of the body data is.
            
        ** Transaction ID **
            64 bits transaction ID is a random number for distinguishing
            different messages.
            
        ** Count & Index **:
            If data type is a fragment message (or respond), there is a field
            'count' following the transaction ID, which indicates the message
            was split to how many fragments; and there is another field 'offset'
            following the 'count'; after them is the message fragment.
"""


class Header(Data):

    def __init__(self, data: bytes, head_len: int, data_type: DataType, sn: TransactionID, pages: int=1, offset: int=0):
        """
        Create package header

        :param data:      header data as bytes
        :param head_len:  length of header (in bytes)
        :param data_type: package body data type
        :param sn:        transaction ID
        :param pages:     fragment count [OPTIONAL], default is 1
        :param offset:    fragment index [OPTIONAL], default is 0
        """
        super().__init__(data=data)
        self.__length = head_len
        self.__type = data_type
        self.__sn = sn
        self.__pages = pages
        self.__offset = offset

    def __str__(self):
        clazz = self.__class__.__name__
        dt = self.data_type
        if dt == MessageFragment:
            # fragment
            pages = self.pages
            offset = self.offset
            return '<%s: %d, "%s" pages=%d offset=%d />' % (clazz, self.length, dt, pages, offset)
        else:
            return '<%s: %d, "%s" />' % (clazz, self.length, dt)

    @property
    def length(self) -> int:
        """ header length in bytes """
        return self.__length

    @property
    def data_type(self) -> DataType:
        return self.__type

    @property
    def trans_id(self) -> TransactionID:
        return self.__sn

    @property
    def pages(self) -> int:
        """ fragment count """
        return self.__pages

    @property
    def offset(self) -> int:
        """ fragment index"""
        return self.__offset

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 12:
            # raise AssertionError('package error: %s' % data)
            return None
        if data[:3] != b'DIM':
            # raise AssertionError('not a DIM package: %s' % data)
            return None
        # get header length & data type
        ch = data[3]
        head_len = (ch & 0xF0) >> 2  # in bytes
        data_type = ch & 0x0F
        data_type = DataType.new(value=data_type)
        assert data_type is not None, 'data type error'
        pos = 4
        # get transaction ID
        sn = TransactionID.parse(data=data[pos:])
        assert sn is not None, 'transaction ID error'
        pos += sn.length
        # get fragments count & offset
        if data_type == MessageFragment:
            assert head_len == 20, 'head length error: %d' % head_len
            assert data_len > head_len, 'fragment package error: %s' % data
            pages = bytes_to_int(data[pos:pos+4])
            offset = bytes_to_int(data[pos+4:pos+8])
            pos += 8
            assert pages > 1 and pages > offset, 'pages error: %d, %d' % (pages, offset)
        else:
            assert head_len == 12, 'head length error: %d' % head_len
            pages = 1
            offset = 0
        return cls(data=data[:pos], head_len=head_len, data_type=data_type, sn=sn, pages=pages, offset=offset)

    @classmethod
    def new(cls, data_type: DataType, sn: TransactionID=None, pages: int=1, offset: int=0):
        if data_type == MessageFragment:
            # fragments
            assert pages > 1 and pages > offset, 'pages error: %d, %d' % (pages, offset)
            options = uint32_to_bytes(value=pages) + uint32_to_bytes(value=offset)
            head_len = 20  # in bytes
        else:
            assert pages == 1 and offset == 0, 'pages error: %d, %d' % (pages, offset)
            options = b''
            head_len = 12  # in bytes
        if sn is None:
            # generate transaction ID
            sn = TransactionID.new()
        # generate header data
        hl_ty = (head_len << 2) | (data_type.value & 0x0F)
        hl_ty = uint8_to_bytes(hl_ty & 0xFF)
        data = b'DIM' + hl_ty + sn.data + options
        return cls(data=data, head_len=head_len, data_type=data_type, sn=sn, pages=pages, offset=offset)


class Package(Data):

    """
        Max Length for Package Body
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MTU      : 576 bytes
        IP Head  : 20 bytes
        UDP Head : 8 bytes
        Header   : 12 bytes (excludes 'pages' and 'offset')
        Reserved : 24 bytes (includes 'pages' and 'offset')
    """
    MAX_BODY_LEN = 512

    def __init__(self, data: bytes, head: Header, body: bytes):
        super().__init__(data=data)
        self.__head = head
        self.__body = body

    def __str__(self):
        clazz = self.__class__.__name__
        body_len = len(self.body)
        return '<%s: head=%s body_len=%d />' % (clazz, self.head, body_len)

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
            # raise AssertionError('package head error')
            return None
        # get package body
        body = data[head.length:]
        return cls(data=data, head=head, body=body)

    @classmethod
    def new(cls, data_type: DataType, sn: TransactionID=None, pages: int=1, offset: int=0, body: bytes=b''):
        # create package with header
        head = Header.new(data_type=data_type, sn=sn, pages=pages, offset=offset)
        data = head.data + body
        return cls(data=data, head=head, body=body)

    def split(self) -> list:
        """
        Split large message package

        :return: message fragment packages
        """
        head = self.head
        body = self.body
        # check data type
        assert head.data_type == Message, 'cannot split this type: %s' % head.data_type
        # split body
        fragments = []
        count = 1
        start = 0
        end = self.MAX_BODY_LEN
        body_len = len(body)
        while end < body_len:
            fragments.append(body[start:end])
            start = end
            end += self.MAX_BODY_LEN
            count += 1
        if start > 0:
            fragments.append(body[start:])  # the tail
        else:
            fragments.append(body)
        # create packages with fragments
        data_type = MessageFragment
        sn = head.trans_id
        packages = []
        for index in range(count):
            body = fragments[index]
            pack = self.new(data_type=data_type, sn=sn, pages=count, offset=index, body=body)
            packages.append(pack)
        return packages

    @classmethod
    def sort(cls, packages: list) -> list:
        packages.sort(key=lambda pack: pack.head.offset)
        return packages

    @classmethod
    def join(cls, packages: list):  # -> Optional[Package]:
        """
        Join sorted packages' body data together

        :param packages: packages sorted by offset
        :return: original message package
        """
        assert len(packages) > 1, 'packages count error: %d' % len(packages)
        first = packages[0]
        assert isinstance(first, Package), 'first package error: %s' % first
        sn = first.head.trans_id
        # get fragments count
        pages = first.head.pages
        if pages != len(packages):
            raise ValueError('pages error: %d, %d' % (pages, len(packages)))
        # add message fragments part by part
        offset = 0
        data = bytearray()
        for item in packages:
            assert isinstance(item, Package), 'package error: %s' % item
            assert item.head.data_type == MessageFragment, 'data type not fragment: %s' % item
            assert item.head.trans_id == sn, 'transaction ID not match: %s' % item
            assert item.head.pages == pages, 'pages error: %s' % item
            assert item.head.offset == offset, 'fragment missed: %d, %s' % (offset, item)
            data += item.body
            offset += 1
        assert offset == pages, 'fragment error: %d/%d' % (offset, pages)
        # OK
        return cls.new(data_type=Message, sn=sn, body=bytes(data))
