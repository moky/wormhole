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
from typing import Union, Optional

from .data import bytes_to_int
from .protocol import Package
from .protocol import Command, CommandRespond
from .protocol import Message, MessageRespond, MessageFragment


class Departure:
    """
        Package(s) to sent out (waiting response)
    """

    EXPIRES = 60  # 2 minutes

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


class Pool:

    def __init__(self):
        super().__init__()
        # waiting list for responding
        self.__departures = []
        # waiting list for processing
        self.__arrivals = []
        # thread locks
        self.__departures_lock = threading.RLock()
        self.__arrivals_lock = threading.RLock()

    #
    #   Departures
    #
    def departures_count(self) -> int:
        with self.__departures_lock:
            return len(self.__departures)

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

    def new_departure(self, payload: Union[Package, list], destination: tuple, source: Union[tuple, int]) -> Departure:
        task = Departure(payload=payload, destination=destination, source=source)
        return self.add_departure(task)

    def del_departure(self, response: Package) -> int:
        count = 0
        head = response.head
        body = response.body
        body_len = len(body)
        data_type = head.data_type
        trans_id = head.trans_id
        if data_type == CommandRespond:
            assert body_len == 0, 'CommandRespond should has no body'
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
            if body_len == 8:
                # Message Fragment Response
                pages = bytes_to_int(body[:4])
                offset = bytes_to_int(body[4:])
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
            else:
                assert body_len == 0, 'MessageRespond body error: %s' % body
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

    def new_arrival(self, data: bytes, source: tuple, destination: tuple) -> Arrival:
        task = Arrival(payload=data, source=source, destination=destination)
        return self.add_arrival(task)
