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

    Data format in UDP payload
"""

from typing import Optional

from .data import Data, UInt8Data, UInt32Data
from .data import random_bytes
from .data import uint8_to_bytes, uint32_to_bytes

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
        Fragment Message         : 0x0A (0000 1010)
"""


class DataType:

    def __init__(self, value: int, name: str='Unknown Type'):
        super().__init__()
        self.__value = value
        self.__name = name
        s_data_types[value] = self

    def __str__(self):
        clazz = self.__class__.__name__
        return '<%s: 0x%04X "%s" />' % (clazz, self.value, self.__name)

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

    @classmethod
    def parse(cls, data: bytes):
        data_len = len(data)
        if data_len < 8:
            raise ValueError('transaction ID length error: %d' % data_len)
        elif data_len > 8:
            data = data[:8]
        return cls(data=data)

    @classmethod
    def new(cls):
        data = random_bytes(8)
        return cls(data=data)


"""
    Package Header:
    
         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      'W'      |      'H'      |    Version    | H-Len |  Type |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Transaction ID (64 bits)                    
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                             Transaction ID (64 bits)                   |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |               Fragment count (32 bits) OPTIONAL               |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |               Fragment index (32 bits) OPTIONAL               |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        
        ** Magic Code **:
            Always be 'WH' (wormhole)
            
        ** Version **:
            Now is 0 (0x00)
            
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


class Header:

    def __init__(self, data: bytes, version: int, length: int, data_type: DataType, sn: TransactionID,
                 pages: int=1, offset: int=0):
        """
        Create package header

        :param data:      package data
        :param version:   package version
        :param length:    package header length (in bytes)
        :param data_type: package body data type
        :param sn:        transaction ID
        :param pages:     fragment count [OPTIONAL], default is 1
        :param offset:    fragment index [OPTIONAL], default is 0
        """
        super().__init__()
        self.__data = data
        self.__version = version
        self.__length = length
        self.__type = data_type
        self.__sn = sn
        self.__pages = pages
        self.__offset = offset

    def __str__(self):
        clazz = self.__class__.__name__
        ver = '0x%02X' % self.version
        dt = self.data_type
        if dt == MessageFragment:
            # fragment
            pages = self.pages
            offset = self.offset
            return '<%s: %s "%s" pages=%d offset=%d />' % (clazz, ver, dt, pages, offset)
        else:
            return '<%s: %s "%s" />' % (clazz, ver, dt)

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def version(self) -> int:
        return self.__version

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
        if data_len < 12 or data[0] != 'W' or data[1] != 'H':
            return AssertionError('package error: %s' % data)
        # get version
        version = data[2]
        if version != 0:
            return ValueError('version error: %d' % version)
        # get header length & data type
        ch = data[3]
        prefix = data[:4]
        data = data[4:]
        head_len = (ch & 0xF0) >> 2  # in bytes
        data_type = ch & 0x0F
        _type = DataType.new(value=data_type)
        # get transaction ID
        _sn = TransactionID.parse(data=data)
        if _sn is None:
            return None
        else:
            data = data[_sn.length:]
        # get fragments count & offset
        if _type == MessageFragment:
            assert head_len == 20, 'head length error: %d' % head_len
            assert data_len > head_len, 'fragment package error: %s' % data
            _pages = UInt32Data.from_bytes(data=data[:4])
            _offset = UInt32Data.from_bytes(data=data[4:8])
            # build data
            data = prefix + _sn.data + _pages.data + _offset.data
            return cls(data=data, version=version, length=head_len, data_type=_type, sn=_sn,
                       pages=_pages.value, offset=_offset.value)
        else:
            assert head_len == 12, 'head length error: %d' % head_len
            # build data
            data = prefix + _sn.data
            return cls(data=data, version=version, length=head_len, data_type=_type, sn=_sn,
                       pages=1, offset=0)

    @classmethod
    def new(cls, data_type: DataType, sn: TransactionID, version: int=0, pages: int=1, offset: int=0):
        if data_type == MessageFragment:
            # fragments
            assert pages > 1 and pages > offset, 'pages error: %d, %d' % (pages, offset)
            options = uint32_to_bytes(value=pages) + uint32_to_bytes(value=offset)
            head_len = 20  # in bytes
        else:
            assert pages == 1 and offset == 0, 'pages error: %d, %d' % (pages, offset)
            options = b''
            head_len = 12  # in bytes
        # version
        ver = UInt8Data.from_uint8(value=version)
        # header length & data type
        hl_ty = (head_len << 2) & (data_type.value & 0x0F)
        hl_ty = uint8_to_bytes(hl_ty & 0xFF)
        data = b'WH' + ver.data + hl_ty + sn.data + options
        return cls(data=data, version=version, length=head_len, data_type=data_type, sn=sn,
                   pages=pages, offset=offset)


class Package:

    """
        Max length for package body
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MTU     : 576 bytes
        IP      : 20 bytes
        UDP     : 8 bytes
        Header  : 8-16 bytes (includes 'pages' and 'offset')
        Reserved: 20-28 bytes (includes 'pages' and 'offset')
    """
    MAX_BODY_LEN = 512

    def __init__(self, data: bytes, head: Header, body: bytes):
        super().__init__()
        self.__data = data
        self.__head = head
        self.__body = body

    def __str__(self):
        clazz = self.__class__.__name__
        body_len = len(self.body)
        return '<%s: head=%s body_len=%d />' % (clazz, self.head, body_len)

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
        # get package body
        body = data[head.length:]
        return Package(data=data, head=head, body=body)

    @classmethod
    def new(cls, data_type: DataType, sn: TransactionID=None, body: bytes=b'', version: int=0):
        assert data_type != MessageFragment, 'data type error: %s' % data_type
        if sn is None:
            # generate sequence number
            sn = TransactionID.new()
        # create package with header
        head = Header.new(version=version, data_type=data_type, sn=sn)
        data = head.data + body
        pack = cls(data=data, head=head, body=body)
        # check body length
        body_len = len(body)
        if body_len <= cls.MAX_BODY_LEN or data_type in [Command, CommandRespond]:
            # command package will never be split
            return pack
        assert data_type in [Message, MessageRespond], 'data type error: %s' % data_type
        return cls.split(package=pack)

    @classmethod
    def split(cls, package) -> list:
        head = package.head
        body = package.body
        # change data type
        assert head.data_type == Message, 'cannot split this type: %s' % head.data_type
        # split body
        fragments = []
        count = 1
        body_len = len(body)
        while body_len > cls.MAX_BODY_LEN:
            fragments.append(body[:cls.MAX_BODY_LEN])
            body = body[cls.MAX_BODY_LEN:]
            body_len -= cls.MAX_BODY_LEN
            count += 1
        fragments.append(body)  # the tail
        # create packages with fragments
        version = head.version
        data_type = MessageFragment
        sn = head.sequence_number
        index = 0
        array = []
        while index < count:
            head = Header.new(version=version, data_type=data_type, sn=sn, pages=count, offset=index)
            data = head.data + body
            pack = cls(data=data, head=head, body=body)
            array.append(pack)
            index += 1
        return array

    @classmethod
    def sort(cls, packages: list) -> list:
        packages.sort(key=lambda pack: pack.head.offset)
        return packages

    @classmethod
    def join(cls, packages: list) -> Optional[bytes]:
        """
        Join all packages' body data together

        :param packages: packages will be sort by offset
        :return: original message data
        """
        # 1. sort it first
        packages = cls.sort(packages)
        first = packages[0]
        sn = first.head.sequence_number
        # 2. get fragments count
        pages = first.head.pages
        if pages != len(packages):
            raise ValueError('pages error: %d, %d' % (pages, len(packages)))
        # 3. add one by one
        offset = 0
        data = bytearray()
        for item in packages:
            assert item.head.data_type == MessageFragment, 'data type not fragment: %s' % item
            assert item.head.sequence_number == sn, 'sequence number not match: %s' % item
            assert item.head.pages == pages, 'pages error: %s' % item
            # check offset
            if item.head.offset != offset:
                raise LookupError('fragment missed: %d' % offset)
            data.append(item.body)
            offset += 1
        if offset != pages:
            raise LookupError('fragment error: %d/%d' % (offset, pages))
        # OK
        return bytes(data)
