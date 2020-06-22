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
    Task
    ~~~~

    Departure - package(s) to be sent out
    Arrival - package data received
    Assemble - message fragments to be joined together
"""

import time
from typing import Union

from .protocol import Package, MessageFragment


class Departure:
    """
        Package(s) to sent out (waiting response)
    """

    def __init__(self, packages: list, destination: tuple, source: Union[tuple, int]=0):
        super().__init__()
        self.packages = packages
        self.destination = destination
        self.source = source
        self.max_retries = 5
        self.last_time = 0  # last send/receive time
        # package header info
        assert len(packages) > 0, 'departure packages should not be empty'
        first = packages[0]
        self.trans_id = first.head.trans_id
        self.data_type = first.head.data_type

    def update_last_time(self):
        self.last_time = time.time()


class Arrival:
    """
        Data package received (waiting process)
    """

    def __init__(self, payload: bytes, source: tuple, destination: tuple):
        super().__init__()
        self.payload = payload
        self.source = source
        self.destination = destination


class Assemble:
    """
        Message fragments received (waiting assemble)
    """

    def __init__(self, fragment: Package, source: tuple, destination: tuple):
        super().__init__()
        self.__fragments = [fragment]
        self.source = source
        self.destination = destination
        self.last_time = 0  # last receive time
        # package header info
        assert fragment.head.data_type == MessageFragment, 'fragment data type error: %s' % fragment
        assert fragment.head.pages > 1, 'fragment pages error: %s' % fragment
        self.trans_id = fragment.head.trans_id
        self.pages = fragment.head.pages
        self.update_last_time()

    @property
    def fragments(self) -> list:
        return self.__fragments

    @property
    def is_completed(self) -> bool:
        return len(self.__fragments) == self.pages

    def update_last_time(self):
        self.last_time = time.time()

    def insert(self, fragment: Package, source: tuple, destination: tuple) -> bool:
        assert source == self.source, 'source error: %s -> %s' % (source, self.source)
        assert destination == self.destination, 'destination error: %s -> %s' % (destination, self.destination)
        count = len(self.__fragments)
        assert count > 0, 'fragments error'
        head = fragment.head
        offset = head.offset
        assert head.data_type == MessageFragment, 'data type error: %s' % head
        assert head.trans_id == self.trans_id, 'transaction ID not match: %s' % head
        assert head.pages == self.pages, 'pages error: %s' % head
        assert head.pages > offset, 'offset error: %s' % head
        index = count
        while index > 0:
            index -= 1
            item = self.__fragments[index]
            if offset < item.head.offset:
                continue
            elif offset == item.head.offset:
                # assert False, 'duplicated: %s' % head
                return False
            # got the position, insert after it
            index += 1
            break
        self.__fragments.insert(index, fragment)
        self.update_last_time()
        return True
