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
from .protocol import Package
from .protocol import Command, CommandRespond
from .protocol import Message, MessageRespond, MessageFragment


class Departure:
    """
        Package(s) to sent out (waiting response)
    """

    EXPIRES = 60  # 1 minute

    def __init__(self, payload: Union[Package, list], destination: tuple, source: Union[tuple, int]=0):
        super().__init__()
        self.payload = payload
        self.destination = destination
        self.source = source
        self.max_retries = 5
        self.last_time = 0

    @property
    def is_expired(self) -> bool:
        return (self.last_time + self.EXPIRES) < time.time()


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

    EXPIRES = 60  # 1 minutes

    def __init__(self, fragment: Package):
        super().__init__()
        self.__fragments = [fragment]
        self.pages = fragment.head.pages
        assert self.pages > 1, 'fragment pages error: %s' % fragment.head
        self.last_time = time.time()

    @property
    def fragments(self) -> list:
        return self.__fragments

    @property
    def is_expired(self) -> bool:
        count = len(self.__fragments)
        assert count > 0, 'fragments error'
        return (self.last_time + self.EXPIRES * self.pages) < time.time()

    @property
    def is_completed(self) -> bool:
        return len(self.__fragments) == self.pages

    def insert(self, fragment: Package) -> bool:
        count = len(self.__fragments)
        assert count > 0, 'fragments error'
        head = fragment.head
        offset = head.offset
        assert head.data_type == MessageFragment, 'data type error: %s' % head
        assert head.trans_id == self.__fragments[0].head.trans_id, 'transaction ID not match: %s' % head
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
    def add_fragment(self, fragment: Package) -> Optional[bytes]:
        """
        Add a fragment package into the pool for MessageFragment received.
        This will just wait until all fragments with the same 'trans_id' received.
        When all fragments received, they will be sorted and combined to the
        original message, and then return the message's data; if there are still
        some fragments missed, return None.

        :param fragment: message fragment
        :return: message data when all fragments received
        """
        raise NotImplemented

    @abstractmethod
    def discard_fragments(self) -> int:
        """
        Remove all expired fragments that belong to the incomplete messages,
        which had waited a long time but still some fragments missed.

        :return: removed message count
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

    def del_departure(self, response: Package) -> int:
        count = 0
        head = response.head
        body = response.body
        body_len = len(body)
        data_type = head.data_type
        trans_id = head.trans_id
        if data_type == CommandRespond:
            assert body_len == 0 or body == b'OK', 'CommandRespond error: %s' % body
            with self.__departures_lock:
                pos = len(self.__departures)
                while pos > 0:
                    pos -= 1
                    pack = self.__departures[pos].payload
                    if not isinstance(pack, Package):
                        continue
                    head = pack.head
                    if head.trans_id != trans_id:
                        continue
                    assert head.data_type == Command, 'task payload not a Command: %s' % pack
                    # Got it!
                    self.__departures.pop(pos)
                    count += 1
        elif data_type == MessageRespond:
            if body_len >= 8:
                # respond for message fragment
                assert body_len == 8 or body[8:] == b'OK', 'MessageRespond error: %s' % body
                # Message Fragment Response
                pages = bytes_to_int(body[:4])
                offset = bytes_to_int(body[4:8])
                assert pages > 1 and pages > offset, 'pages error: %d, %d' % (pages, offset)
                with self.__departures_lock:
                    pos = len(self.__departures)
                    while pos > 0:
                        pos -= 1
                        packages = self.__departures[pos].payload
                        if not isinstance(packages, list):
                            continue
                        index = len(packages)
                        while index > 0:
                            index -= 1
                            pack = packages[index]
                            head = pack.head
                            if head.trans_id != trans_id:
                                break
                            assert head.data_type == MessageFragment, 'data type should be a Fragment: %s' % pack
                            assert head.pages == pages, 'pages not match: %d, %s' % (pages, head)
                            if head.offset == offset:
                                # Got it!
                                packages.pop(index)
                                count += 1
                        if len(packages) == 0:
                            # all fragment sent, remove this task
                            self.__departures.pop(pos)
            elif body_len == 0 or body == b'OK':
                # respond for entire message
                with self.__departures_lock:
                    pos = len(self.__departures)
                    while pos > 0:
                        pos -= 1
                        pack = self.__departures[pos].payload
                        if not isinstance(pack, Package):
                            continue
                        head = pack.head
                        if head.trans_id != trans_id:
                            continue
                        assert head.data_type == Message, 'task payload not a Message: %s' % pack
                        # Got it!
                        self.__departures.pop(pos)
                        count += 1
            else:
                # respond for split message
                assert body == b'AGAIN', 'MessageRespond error: %s' % body
                # TODO: resend all fragments of this message
        else:
            assert False, 'data type should be a Respond: %s' % response
        return count

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
    def add_fragment(self, fragment: Package) -> Optional[bytes]:
        data = None
        with self.__fragments_lock:
            trans_id = fragment.head.trans_id
            assemble = self.__fragments.get(trans_id)
            if assemble is None:
                self.__fragments[trans_id] = Assemble(fragment=fragment)
            elif assemble.insert(fragment=fragment) and assemble.is_completed:
                data = Package.join(packages=assemble.fragments)
                self.__fragments.pop(trans_id)
        return data

    def discard_fragments(self) -> int:
        """
        Remove all expired fragments

        :return:
        """
        count = 0
        with self.__fragments_lock:
            keys = list(self.__fragments.keys())
            for trans_id in keys:
                assemble = self.__fragments.get(trans_id)
                if assemble is None:
                    # error
                    self.__fragments.pop(trans_id)
                    count += 1
                elif assemble.is_expired:
                    # remove expired fragments
                    self.__fragments.pop(trans_id)
                    count += 1
        return count
