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

from .tlv import Data
from .protocol import DataType, TransactionID, Message, MessageFragment
from .header import Header


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

    def __init__(self, head: Header, body: Data = None, data=None):
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
    def new(cls, data_type: DataType, sn: TransactionID = None, pages: int = 1, offset: int = 0,
            body_length: int = -1, body: Data = None):
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
