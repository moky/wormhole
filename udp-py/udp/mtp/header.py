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

from typing import Optional, Union

from ..ba import ByteArray, Data, Convert, MutableData

from .protocol import DataType, TransactionID

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
            and there is another field 'index' following the 'count'.

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

    def __init__(self, data: Union[bytes, bytearray, ByteArray],
                 data_type: DataType, sn: TransactionID, pages: int = 1, index: int = 0, body_length: int = -1):
        """
        Create package header

        :param data:      bytes, bytearray, Data or Header object
        :param data_type: package body data type
        :param sn:        transaction ID
        :param pages:     fragment count [OPTIONAL], default is 1
        :param index:     fragment index [OPTIONAL], default is 0
        :param body_length: length of body, default is -1 (unlimited)
        """
        if isinstance(data, ByteArray):
            super().__init__(buffer=data.buffer, offset=data.offset, size=data.size)
        else:
            super().__init__(buffer=data)
        self.__type = data_type
        self.__sn = sn
        self.__pages = pages
        self.__index = index
        self.__body_size = body_length

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        dt = self.data_type
        bl = self.body_length
        return '<%s: %d, "%s" pages=%d, index=%d, body_len=%d />' % (clazz, self.size, dt, self.pages, self.index, bl)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        dt = self.data_type
        bl = self.body_length
        return '<%s: %d, "%s" pages=%d, index=%d, body_len=%d />' % (clazz, self.size, dt, self.pages, self.index, bl)

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
    def index(self) -> int:
        """ fragment index"""
        return self.__index

    @property
    def body_length(self) -> int:
        return self.__body_size

    @classmethod
    def parse(cls, data: ByteArray):  # -> Header:
        data_type = get_data_type(data=data)
        if data_type is None:
            # not a DIM package?
            return None
        head_len = get_header_length(data=data)
        if data.size < head_len:
            # waiting for more data
            return None
        pages = 1
        index = 0
        body_len = -1
        if head_len == 4:
            """ simple header (for UDP only)
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            """
            sn = TransactionID.ZERO
        elif head_len == 8:
            """ simple header with body length
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |                 Body Length (32 bits) OPTIONAL                |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            """
            sn = TransactionID.ZERO
            body_len = Convert.int32_from_data(data=data, start=4)
        elif head_len == 12:
            """ command/message header without body length (for UDP only)
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |                    Transaction ID (64 bits)                    
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                     Transaction ID (64 bits)                   |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            """
            sn = TransactionID.from_data(data=data.slice(start=4, end=12))
        elif head_len == 16:
            """ command/message header with body length
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |                    Transaction ID (64 bits)                    
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                     Transaction ID (64 bits)                   |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |                 Body Length (32 bits) OPTIONAL                |
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            """
            sn = TransactionID.from_data(data=data.slice(start=4, end=12))
            body_len = Convert.int32_from_data(data=data, start=12)
        elif head_len == 20:
            """ fragment header without body length (for UDP only)
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
            """
            sn = TransactionID.from_data(data=data.slice(start=4, end=12))
            pages = Convert.int32_from_data(data=data, start=12)
            index = Convert.int32_from_data(data=data, start=16)
        elif head_len == 24:
            """ fragment header with body length
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
            """
            sn = TransactionID.from_data(data=data.slice(start=4, end=12))
            pages = Convert.int32_from_data(data=data, start=12)
            index = Convert.int32_from_data(data=data, start=16)
            body_len = Convert.int32_from_data(data=data, start=20)
        else:
            # raise ValueError('header length error: %d' % head_len)
            return None
        # if sn is None:
        #     # raise ValueError('header length error: %d' % head_len)
        #     return None
        if pages < 1 or pages > cls.MAX_PAGES:
            # raise ValueError('pages error: %d' % pages)
            return None
        if index < 0 or index >= pages:
            # raise ValueError('index error: %d' % index)
            return None
        if body_len < -1 or body_len > cls.MAX_BODY_LENGTH:
            # raise ValueError('body length error: %d' % body_len)
            return None
        # create header
        return cls(data=data.slice(start=0, end=head_len),
                   data_type=data_type, sn=sn, pages=pages, index=index, body_length=body_len)

    @classmethod
    def new(cls, data_type: DataType,
            sn: Optional[TransactionID] = None, pages: int = 1, index: int = 0, body_length: int = -1):
        head_len = 4  # in bytes
        # transaction ID
        if sn is None:
            # generate transaction ID
            sn = TransactionID.generate()
            head_len += 8
        elif sn != TransactionID.ZERO:
            head_len += 8
        # pages & index
        if data_type.is_message_fragment or data_type.is_message_response:
            # message fragment (or its respond)
            assert pages > index, 'pages error: %d, %d' % (pages, index)
            d1 = Convert.uint32data_from_value(value=pages)
            d2 = Convert.uint32data_from_value(value=index)
            options = d1.concat(d2)
            head_len += 8
        else:
            # command/message (or its respond)
            assert pages == 1 and index == 0, 'pages error: %d, %d' % (pages, index)
            options = None
        # body length
        if body_length >= 0:
            d3 = Convert.uint32data_from_value(value=body_length)
            if options is None:
                options = d3
            else:
                options = options.concat(d3)
            head_len += 4
        # generate header data
        hl_ty = (head_len << 2) | (data_type.value & 0x0F)
        data = MutableData(capacity=head_len)
        data.append(source=cls.MAGIC_CODE)  # 'DIM'
        data.push(element=hl_ty)
        if sn != TransactionID.ZERO:
            data.append(source=sn)
        if options is not None:
            data.append(source=options)
        return cls(data=data, data_type=data_type, sn=sn, pages=pages, index=index, body_length=body_length)


def get_data_type(data: ByteArray) -> Optional[DataType]:
    if data.size < 4:
        # waiting for more data
        return None
    buffer = data.buffer
    offset = data.offset
    if buffer[offset:(offset+3)] != Header.MAGIC_CODE:
        # raise ValueError('not a DIM package: %s' % data)
        return None
    return DataType.from_data(data=data.slice(start=3, end=4))


def get_header_length(data: ByteArray) -> int:
    # header length shared the byte with data type
    ch = data.get_byte(index=3)
    hl = (ch & 0xF0) >> 4
    if hl < 1 or hl > 6:
        return 0
    else:
        return hl << 2  # in bytes
