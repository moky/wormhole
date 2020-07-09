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

from ..tlv.utils import random_bytes, bytes_to_int
from ..tlv import Data, UInt32Data, MutableData

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
        |                 Body Length (32 bits) OPTIONAL                |
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
            If data type is a fragment message (or its respond),
            there is a field 'count' following the transaction ID,
            which indicates the message was split to how many fragments;
            and there is another field 'offset' following the 'count'.
        
        ** Body Length **:
            Defined only for TCP stream.
            If transfer by UDP, no need to define the body's length.
"""


class Header(Data):

    """
        Max Length for message package body
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Each message package before split should not more than 1GB,
        so the max pages should not more than about 2,000,000.
    """
    MAX_BODY_LENGTH = 1024 * 1024 * 1024  # 1GB
    MAX_PAGES = 1024 * 1024 * 2           # 1GB

    MAGIC_CODE = b'DIM'

    def __init__(self, data,
                 data_type: DataType, sn: TransactionID,
                 pages: int=1, offset: int=0, body_length: int=-1):
        """
        Create package header

        :param data:      bytes, bytearray, Data or Header object
        :param data_type: package body data type
        :param sn:        transaction ID
        :param pages:     fragment count [OPTIONAL], default is 1
        :param offset:    fragment index [OPTIONAL], default is 0
        :param body_length: length of body, default is -1 (unlimited)
        """
        super().__init__(data=data)
        if isinstance(data, Header):
            self.__type = data.__type
            self.__sn = data.__sn
            self.__pages = data.__pages
            self.__offset = data.__offset
            self.__body_len = data.__body_len
        else:
            assert isinstance(data, Data), 'head data error: %s' % data
            self.__type = data_type
            self.__sn = sn
            self.__pages = pages
            self.__offset = offset
            self.__body_len = body_length

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        dt = self.data_type
        if dt == MessageFragment:
            # fragment
            pages = self.pages
            offset = self.offset
            return '<%s: %d, "%s" pages=%d offset=%d />' % (clazz, self.length, dt, pages, offset)
        else:
            return '<%s: %d, "%s" />' % (clazz, self.length, dt)

    def __repr__(self) -> str:
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
    def data_type(self) -> DataType:
        return self.__type

    @property
    def sn(self) -> TransactionID:
        return self.__sn

    @property
    def pages(self) -> int:
        """ fragment count """
        return self.__pages

    @property
    def offset(self) -> int:
        """ fragment index"""
        return self.__offset

    @property
    def body_length(self) -> int:
        return self.__body_len

    @classmethod
    def parse(cls, data: Data):  # -> Header:
        if data._length < 4:
            # raise AssertionError('package error: %s' % data)
            return None
        if data.get_byte(index=0) != cls.MAGIC_CODE[0] or \
                data.get_byte(index=1) != cls.MAGIC_CODE[1] or \
                data.get_byte(index=2) != cls.MAGIC_CODE[2]:
            # raise AssertionError('not a DIM package: %s' % data)
            return None
        # get header length & data type
        ch = data.get_byte(index=3)
        head_len = (ch & 0xF0) >> 2  # in bytes
        sn = None
        pages = 1
        offset = 0
        body_len = -1
        if head_len == 4:
            # simple header
            sn = TransactionID.ZERO
        elif head_len == 8:
            # simple header with body length
            sn = TransactionID.ZERO
            body_len = data.get_uint32_value(start=4)
        elif head_len >= 12:
            # command/message/fragment header
            sn = TransactionID.parse(data=data.slice(start=4))
            if head_len == 16:
                # command/message header with body length
                body_len = data.get_uint32_value(start=12)
            elif head_len >= 20:
                # fragment header
                pages = data.get_uint32_value(start=12)
                offset = data.get_uint32_value(start=16)
                if head_len == 24:
                    # fragment header with body length
                    body_len = data.get_uint32_value(start=20)
        if sn is None:
            # raise AssertionError('head length error: %d' % head_len)
            return None
        if pages < 1 or pages > cls.MAX_PAGES:
            # raise ValueError('pages error: %d' % pages)
            return None
        if offset < 0 or offset >= pages:
            # raise ValueError('offset error: %d' % offset)
            return None
        if body_len < -1 or body_len > cls.MAX_BODY_LENGTH:
            # raise ValueError('body length error: %d' % body_len)
            return None
        data_type = ch & 0x0F
        data_type = DataType.new(value=data_type)
        if data_type is None:
            # raise LookupError('data type error: %d' % (ch & 0x0F))
            return None
        return cls(data=data.slice(end=head_len),
                   data_type=data_type, sn=sn, pages=pages, offset=offset, body_length=body_len)

    @classmethod
    def new(cls, data_type: DataType, sn: TransactionID=None, pages: int=1, offset: int=0, body_length: int=-1):
        head_len = 4  # in bytes
        # transaction ID
        if sn is None:
            # generate transaction ID
            sn = TransactionID.generate()
            head_len += 8
        elif sn != TransactionID.ZERO:
            head_len += 8
        # pages & offset
        if data_type == MessageFragment:
            # message fragment (or its respond)
            assert pages > 1 and pages > offset, 'pages error: %d, %d' % (pages, offset)
            d1 = UInt32Data(value=pages)
            d2 = UInt32Data(value=offset)
            options = d1.concat(d2)
            head_len += 8
        else:
            # command/message (or its respond)
            assert pages == 1 and offset == 0, 'pages error: %d, %d' % (pages, offset)
            options = None
        # body length
        if body_length >= 0:
            d3 = UInt32Data(value=body_length)
            if options is None:
                options = d3
            else:
                options = options.concat(d3)
            head_len += 4
        # generate header data
        hl_ty = (head_len << 2) | (data_type.value & 0x0F)
        data = MutableData(capacity=head_len)
        data.append(cls.MAGIC_CODE)  # b'DIM'
        data.append(hl_ty)
        if sn != TransactionID.ZERO:
            data.append(sn)
        if options is not None:
            data.append(options)
        return cls(data=data, data_type=data_type, sn=sn, pages=pages, offset=offset, body_length=body_length)


class Package(Data):

    """
        Optimal Length for UDP Package Body
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MTU      : 576 bytes
        IP Head  : 20 bytes
        UDP Head : 8 bytes
        Header   : 12 bytes (excludes 'pages', 'offset' and 'bodyLen')
        Reserved : 24 bytes (includes 'pages', 'offset' and 'bodyLen')
    """
    OPTIMAL_BODY_LENGTH = 512

    def __init__(self, head: Header, body: Data=None, data=None):
        if data is None:
            if body is None:
                body = Data.ZERO
                data = head
            else:
                data = head.concat(body)
        elif body is None:
            body = Data.ZERO
        super().__init__(data=data)
        self.__head = head
        self.__body = body

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: head=%s body_len=%d />' % (clazz, self.head, self.body.length)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s: head=%s body_len=%d />' % (clazz, self.head, self.body.length)

    @property
    def head(self) -> Header:
        return self.__head

    @property
    def body(self) -> Data:
        return self.__body

    @classmethod
    def parse(cls, data: Data):  # -> Package
        # get package head
        head = Header.parse(data=data)
        if head is None:
            # raise AssertionError('package head error')
            return None
        # check lengths
        data_len = data.length
        head_len = head.length
        body_len = head.body_length
        if body_len < 0:
            # unlimited
            body_len = data_len - head_len
        pack_len = head_len + body_len
        if data_len < pack_len:
            # raise ValueError('package length error: %s' % data)
            return None
        elif data_len > pack_len:
            data = data.slice(end=pack_len)
        # get body
        if body_len == 0:
            body = Data.ZERO
        else:
            body = data.slice(start=head_len)
        return cls(data=data, head=head, body=body)

    @classmethod
    def new(cls, data_type: DataType, sn: TransactionID=None, pages: int=1, offset: int=0,
            body_length: int=-1, body: Data=None):
        # create package with header
        head = Header.new(data_type=data_type, sn=sn, pages=pages, offset=offset, body_length=body_length)
        return cls(head=head, body=body)

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
        end = self.OPTIMAL_BODY_LENGTH
        body_len = body.length
        while end < body_len:
            fragments.append(body.slice(start=start, end=end))
            start = end
            end += self.OPTIMAL_BODY_LENGTH
            count += 1
        if start > 0:
            fragments.append(body.slice(start=start))  # the tail
        else:
            fragments.append(body)
        # create packages with fragments
        data_type = MessageFragment
        sn = head.sn
        packages = []
        if head.body_length < 0:
            # UDP (unlimited)
            for i in range(count):
                body = fragments[i]
                pack = self.new(data_type=data_type, sn=sn, pages=count, offset=i, body_length=-1, body=body)
                packages.append(pack)
        else:
            # TCP (should not happen)
            for i in range(count):
                body = fragments[i]
                pack = self.new(data_type=data_type, sn=sn, pages=count, offset=i, body_length=body.length, body=body)
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
        count = len(packages)
        assert count > 1, 'packages count error: %d' % count
        first = packages[0]
        assert isinstance(first, Package), 'first package error: %s' % first
        trans_id = first.head.sn
        # get fragments count
        pages = first.head.pages
        assert pages == count, 'pages error: %d, %d' % (pages, count)
        # add message fragments part by part
        index = 0
        data = bytearray()
        for item in packages:
            assert isinstance(item, Package), 'package error: %s' % item
            assert item.head.data_type == MessageFragment, 'data type not fragment: %s' % item
            assert item.head.sn == trans_id, 'transaction ID not match: %s' % item
            assert item.head.pages == pages, 'pages error: %s' % item
            assert item.head.offset == index, 'fragment missed: %d, %s' % (index, item)
            data += item.body.get_bytes()
            index += 1
        assert index == pages, 'fragment error: %d/%d' % (index, pages)
        # OK
        body = Data(data=data)
        if first.head.body_length < 0:
            # UDP (unlimited)
            body_len = -1
        else:
            # TCP (should not happen)
            body_len = body.length
        return cls.new(data_type=Message, sn=trans_id, body_length=body_len, body=body)
