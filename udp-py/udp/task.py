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
    Peer
    ~~~~

    Network Node
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Union, Optional

from .data import bytes_to_int
from .protocol import Package, TransactionID, DataType
from .protocol import Command, CommandRespond
from .protocol import Message, MessageRespond, MessageFragment


class Departure:
    """
        Package(s) to sent out (waiting response)
    """

    """
        Each fragment should wait 1 minute for response
    """
    EXPIRES = 60  # seconds

    def __init__(self, packages: list, destination: tuple, source: Union[tuple, int]=0):
        super().__init__()
        self.packages = packages
        self.destination = destination
        self.source = source
        self.max_retries = 5
        self.last_time = 0

    @property
    def trans_id(self) -> Optional[TransactionID]:
        if len(self.packages) > 0:
            first = self.packages[0]
            assert isinstance(first, Package), 'first package error: %s' % first
            return first.head.trans_id

    @property
    def data_type(self) -> Optional[DataType]:
        if len(self.packages) > 0:
            first = self.packages[0]
            assert isinstance(first, Package), 'first package error: %s' % first
            return first.head.data_type

    @property
    def is_expired(self) -> bool:
        count = len(self.packages)
        expires = self.EXPIRES * (count + 1)
        return (self.last_time + expires) < time.time()


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

    """
        Each fragment should wait 1 minute for receiving
    """
    EXPIRES = 60  # seconds

    def __init__(self, fragment: Package, source: tuple, destination: tuple):
        super().__init__()
        assert fragment.head.data_type == MessageFragment, 'fragment data type error: %s' % fragment
        assert fragment.head.pages > 1, 'fragment pages error: %s' % fragment
        self.__fragments = [fragment]
        self.source = source
        self.destination = destination
        self.last_time = time.time()  # last update time

    @property
    def fragments(self) -> list:
        return self.__fragments

    @property
    def trans_id(self) -> TransactionID:
        assert len(self.__fragments) > 0, 'fragments should not empty'
        return self.__fragments[0].head.trans_id

    @property
    def pages(self) -> int:
        assert len(self.__fragments) > 0, 'fragments should not empty'
        return self.__fragments[0].head.pages

    @property
    def is_expired(self) -> bool:
        count = len(self.__fragments)
        assert count > 0, 'fragments error'
        pages = self.pages
        assert pages >= count, 'pages error: %d, %d' % (pages, count)
        expires = self.EXPIRES * (pages - count + 1)
        return (self.last_time + expires) < time.time()

    @property
    def is_completed(self) -> bool:
        return len(self.__fragments) == self.pages

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
        self.last_time = time.time()
        return True


class Pool(ABC):

    #
    #   Departures
    #

    @abstractmethod
    def get_departure(self) -> Optional[Departure]:
        """
        Gat one departure task from the pool for sending.

        :return: any task
        """
        raise NotImplemented

    @abstractmethod
    def add_departure(self, task: Departure) -> Departure:
        """
        Append a departure task into the pool after sent.
        This should be removed after its response received; if timeout, send it
        again and check it's retries counter, when it's still greater than 0,
        put it back to the pool for resending.

        :param task: departure task
        :return: same task
        """
        raise NotImplemented

    @abstractmethod
    def del_departure(self, response: Package) -> int:
        """
        Delete the departure task with 'trans_id' in the response.
        If it's a message fragment, check the page offset too.

        :param response:
        :return: 0 on task not found
        """
        raise NotImplemented

    #
    #   Arrivals
    #

    @abstractmethod
    def arrivals_count(self) -> int:
        """
        Check how many arrivals waiting in the pool

        :return: arrivals count
        """
        raise NotImplemented

    @abstractmethod
    def get_arrival(self) -> Optional[Arrival]:
        """
        Get one arrival task from the pool for processing

        :return: any task
        """
        raise NotImplemented

    @abstractmethod
    def add_arrival(self, task: Arrival) -> Arrival:
        """
        Append an arrival task into the pool after received something

        :param task: arrival task
        :return: same task
        """
        raise NotImplemented

    #
    #   Fragments Assembling
    #

    @abstractmethod
    def add_fragment(self, fragment: Package, source: tuple, destination: tuple) -> Optional[bytes]:
        """
        Add a fragment package into the pool for MessageFragment received.
        This will just wait until all fragments with the same 'trans_id' received.
        When all fragments received, they will be sorted and combined to the
        original message, and then return the message's data; if there are still
        some fragments missed, return None.

        :param fragment:    message fragment
        :param source:      remote address
        :param destination: local address
        :return: message data when all fragments received
        """
        raise NotImplemented

    @abstractmethod
    def discard_fragments(self) -> list:
        """
        Remove all expired fragments that belong to the incomplete messages,
        which had waited a long time but still some fragments missed.

        :return: assembling list
        """
        raise NotImplemented


class MemPool(Pool):

    def __init__(self):
        super().__init__()
        # waiting list for responding
        self.__departures = []
        self.__departures_lock = threading.Lock()
        # waiting list for processing
        self.__arrivals = []
        self.__arrivals_lock = threading.Lock()
        # waiting list for assembling
        self.__fragments = {}  # TransactionID -> Assemble
        self.__fragments_lock = threading.Lock()

    #
    #   Departures
    #
    def get_departure(self) -> Optional[Departure]:
        with self.__departures_lock:
            if len(self.__departures) > 0:
                # check last sent time
                task = self.__departures[0]
                if task.is_expired:
                    return self.__departures.pop(0)

    def add_departure(self, task: Departure) -> Departure:
        with self.__departures_lock:
            self.__departures.append(task)
        return task

    def __del_entire_task(self, trans_id: TransactionID) -> int:
        count = 0
        with self.__departures_lock:
            pos = len(self.__departures)
            while pos > 0:
                pos -= 1
                task = self.__departures[pos]
                assert isinstance(task, Departure), 'departure task error: %s' % task
                if task.trans_id != trans_id:
                    # transaction ID not match
                    continue
                assert task.data_type in [Command, Message], 'task error: %s' % task
                # Got it!
                self.__departures.pop(pos)
                count += 1
                # break
        return count

    def __del_task_fragment(self, trans_id: TransactionID, pages: int, offset: int) -> bool:
        count = 0
        with self.__departures_lock:
            pos = len(self.__departures)
            while pos > 0:
                pos -= 1
                task = self.__departures[pos]
                assert isinstance(task, Departure), 'departure task error: %s' % task
                if task.trans_id != trans_id:
                    # transaction ID not match
                    continue
                assert task.data_type == MessageFragment, 'task error: %s' % task
                packages = task.packages
                index = len(packages)
                while index > 0:
                    index -= 1
                    pack = packages[index]
                    assert isinstance(pack, Package), 'package error: %s' % packages
                    assert pack.head.trans_id == trans_id, 'task fragment error: %s' % pack.head
                    assert pack.head.data_type == MessageFragment, 'task error: %s' % pack.head
                    assert pack.head.pages == pages, 'pages not match: %d, %s' % (pages, pack.head)
                    if pack.head.offset == offset:
                        # Got it!
                        packages.pop(index)
                        count += 1
                        # break
                if len(packages) == 0:
                    # all fragment sent, remove this task
                    self.__departures.pop(pos)
                # break
        return count

    def del_departure(self, response: Package) -> int:
        head = response.head
        body = response.body
        body_len = len(body)
        data_type = head.data_type
        trans_id = head.trans_id
        if data_type == CommandRespond:
            # response for Command
            assert body_len == 0 or body == b'OK', 'CommandRespond error: %s' % body
            return self.__del_entire_task(trans_id=trans_id)
        elif data_type == MessageRespond:
            # response for Message or Fragment
            if body_len >= 8:
                # MessageFragment
                assert body_len == 8 or body[8:] == b'OK', 'MessageRespond error: %s' % body
                # get pages count and index
                pages = bytes_to_int(body[:4])
                offset = bytes_to_int(body[4:8])
                assert pages > 1 and pages > offset, 'pages error: %d, %d' % (pages, offset)
                return self.__del_task_fragment(trans_id=trans_id, pages=pages, offset=offset)
            elif body_len == 0 or body == b'OK':
                # Message
                return self.__del_entire_task(trans_id=trans_id)
            else:
                # respond for split message
                assert body == b'AGAIN', 'MessageRespond error: %s' % body
                # TODO: resend all fragments of this message
                return 0
        else:
            assert False, 'data type should be a Respond: %s' % data_type

    #
    #   Arrivals
    #
    def arrivals_count(self) -> int:
        with self.__arrivals_lock:
            return len(self.__arrivals)

    def get_arrival(self) -> Optional[Arrival]:
        with self.__arrivals_lock:
            if len(self.__arrivals) > 0:
                return self.__arrivals.pop(0)

    def add_arrival(self, task: Arrival) -> Arrival:
        with self.__arrivals_lock:
            self.__arrivals.append(task)
        return task

    #
    #   Fragments Assembling
    #
    def add_fragment(self, fragment: Package, source: tuple, destination: tuple) -> Optional[bytes]:
        data = None
        with self.__fragments_lock:
            trans_id = fragment.head.trans_id
            assemble = self.__fragments.get(trans_id)
            if assemble is None:
                # create new assemble
                assemble = Assemble(fragment=fragment, source=source, destination=destination)
                self.__fragments[trans_id] = assemble
            else:
                assert isinstance(assemble, Assemble), 'fragments error: %s' % assemble
                # insert fragment and check whether completed
                if assemble.insert(fragment=fragment, source=source, destination=destination):
                    if assemble.is_completed:
                        data = Package.join(packages=assemble.fragments)
                        self.__fragments.pop(trans_id)
        return data

    def discard_fragments(self) -> list:
        """
        Remove all expired fragments

        :return:
        """
        array = []
        with self.__fragments_lock:
            keys = list(self.__fragments.keys())
            for trans_id in keys:
                assemble = self.__fragments.get(trans_id)
                assert isinstance(assemble, Assemble), 'fragments error: %s' % assemble
                if assemble.is_expired:
                    # remove expired fragments
                    array.append(assemble)
                    self.__fragments.pop(trans_id)
        return array
