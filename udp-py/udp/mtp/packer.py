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

from typing import List, Optional

from ..ba import ByteArray, MutableData

from .protocol import DataType, TransactionID
from .package import Package


class Packer:

    def __init__(self, sn: TransactionID, pages: int):
        super().__init__()
        self.__sn = sn
        self.__pages = pages
        # assert sn is not None and pages > 1, 'pages error: %d' % pages
        self.__assembling: List[Package] = []      # message fragments
        self.__complete: Optional[Package] = None  # origin message package

    @property
    def sn(self) -> TransactionID:
        return self.__sn

    @property
    def completed(self) -> bool:
        return len(self.__assembling) == self.__pages

    @property
    def package(self) -> Optional[Package]:
        if self.__complete is None and self.completed:
            self.__complete = self.join(fragments=self.__assembling)
        return self.__complete

    @property
    def fragments(self) -> List[Package]:
        return self.__assembling

    def insert(self, fragment: Package) -> Optional[Package]:
        if self.__complete is not None:
            # already completed
            return self.__complete
        head = fragment.head
        assert head.sn == self.__sn, 'SN not match: %s, %s' % (head.sn, self.__sn)
        assert head.data_type.is_fragment, 'Package only for fragments: %s' % head.data_type
        assert head.pages == self.__pages, 'pages error: %d, %d' % (head.pages, self.__pages)
        assert head.index < self.__pages, 'index error: %d, %d' % (head.index, self.__pages)
        count = len(self.__assembling)
        index = count - 1
        while index >= 0:
            item = self.__assembling[index]
            if item.head.index < head.index:
                # got the position
                break
            elif item.head.index == head.index:
                # raise IndexError('duplicated: %s' % item.head)
                return None
            else:
                index -= 1
        # insert after the position
        self.__assembling.insert(index + 1, fragment)
        return self.package

    """
        Optimal Length for UDP Package Body
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MTU      : 576 bytes
        IP Head  : 20 bytes
        UDP Head : 8 bytes
        Header   : 12 bytes (excludes 'pages', 'index' and 'bodyLen')
        Reserved : 24 bytes (includes 'pages', 'index' and 'bodyLen')
    """
    OPTIMAL_BODY_LENGTH = 512

    @classmethod
    def join(cls, fragments: List[Package]) -> Optional[Package]:
        """
        Join sorted packages' body data together

        :param fragments: fragments sorted by index
        :return: original message package
        """
        count = len(fragments)
        assert count > 1, 'fragments count error: %d' % count
        first = fragments[0]
        sn = first.head.sn
        # get fragments count
        pages = first.head.pages
        assert pages == count, 'pages error: %d, %d' % (pages, count)
        # add message fragments part by part
        array: List[ByteArray] = []
        length = 0
        for index in range(count):
            item = fragments[index]
            assert item.head.data_type.is_fragment, 'data type should be fragment: %s' % item
            assert item.head.sn == sn, 'transaction ID not match: %s' % item
            assert item.head.pages == pages, 'pages error: %s' % item
            assert item.head.index == index, 'fragment missed: %d' % index
            array.append(item.body)
            length += item.body.size
        # join fragments
        body = MutableData(capacity=length)
        for index in range(count):
            body.append(source=array[index])
        if first.head.body_length < 0:
            # UDP (unlimited)
            assert first.head.body_length == -1, 'body length error: %d' % first.head.body_length
            return Package.new(data_type=DataType.MESSAGE, sn=sn, pages=1, index=0, body_length=-1, body=body)
        else:
            return Package.new(data_type=DataType.MESSAGE, sn=sn, pages=1, index=0, body_length=body.size, body=body)

    @classmethod
    def split(cls, package: Package) -> List[Package]:
        """
        Split large message package

        :param package: the large message package
        :return: message fragment packages
        """
        head = package.head
        body = package.body
        # check data type
        assert head.data_type.is_message, 'cannot split this type: %s' % head.data_type
        # split body
        fragments: List[ByteArray] = []
        pages = 1
        start = 0
        end = cls.OPTIMAL_BODY_LENGTH
        body_len = body.size
        while end < body_len:
            fragments.append(body.slice(start=start, end=end))
            pages += 1
            start = end
            end += cls.OPTIMAL_BODY_LENGTH
        if start > 0:
            fragments.append(body.slice(start=start))  # the tail
        else:
            fragments.append(body)  # the whole body (too small)
        # create packages with fragments
        sn = head.sn
        msg_fra = DataType.MESSAGE_FRAGMENT
        packages: List[Package] = []
        if pages == 1:
            # package too small, no need to split
            assert len(fragments) == 1, 'fragments error: %d' % len(fragments)
            packages.append(package)
        elif head.body_length < 0:
            # UDP (unlimited)
            assert head.body_length == -1, 'body length error: %d' % head.body_length
            for index in range(pages):
                data = fragments[index]
                pack = Package.new(data_type=msg_fra, sn=sn, pages=pages, index=index,
                                   body_length=-1, body=data)
                packages.append(pack)
        else:
            # TCP (should not happen)
            for index in range(pages):
                data = fragments[index]
                pack = Package.new(data_type=msg_fra, sn=sn, pages=pages, index=index,
                                   body_length=data.size, body=data)
                packages.append(pack)
        return packages

    @classmethod
    def sort(cls, fragments: List[Package]) -> List[Package]:
        """
        Sort the fragments with head.index

        :param fragments: fragments
        :return sorted fragments
        """
        fragments.sort(key=lambda pack: pack.head.index)
        return fragments
