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

from .tlv import Data, UInt32Data, MutableData
from .protocol import DataType, TransactionID, MessageFragment

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
    MAX_PAGES = 1024 * 1024 * 2  # 1GB

    MAGIC_CODE = b'DIM'

    def __init__(self, data,
                 data_type: DataType, sn: TransactionID,
                 pages: int = 1, offset: int = 0, body_length: int = -1):
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
    def new(cls, data_type: DataType, sn: TransactionID = None, pages: int = 1, offset: int = 0, body_length: int = -1):
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
