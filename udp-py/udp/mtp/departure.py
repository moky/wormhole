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

import threading
import time
import weakref
from typing import Optional, List, Dict

from .protocol import DataType, TransactionID
from .package import Package
from .packer import Packer


"""
    Outgoing Data Package
    ~~~~~~~~~~~~~~~~~~~~~
    
    waiting for response
"""


class Departure:

    # Departure task will be expired after 2 minutes
    # if no response received
    EXPIRES = 120  # seconds

    def __init__(self, packages: List[Package], source: Optional[tuple], destination: tuple):
        super().__init__()
        self.__packages = packages
        first = packages[0]
        head = first.head
        self.__type = head.data_type
        self.__sn = head.sn
        self.__source = source
        self.__destination = destination
        self.__max_retires = 3  # totally 4 times to be sent at the most
        self.__expired = 0      # expired time (timestamp in seconds)
        self.__lock = threading.RLock()

    @property
    def data_type(self) -> DataType:
        return self.__type

    @property
    def sn(self) -> TransactionID:
        return self.__sn

    @property
    def source(self) -> Optional[tuple]:
        return self.__source

    @property
    def destination(self) -> tuple:
        return self.__destination

    def is_expired(self, now: float) -> bool:
        with self.__lock:
            if self.__max_retires >= 0 and self.__expired < now:
                # decrease counter
                self.__max_retires -= 1
                # update expired time
                self.__expired = time.time() + self.EXPIRES
                return True

    @property
    def fragments(self) -> Optional[List[Package]]:
        with self.__lock:
            if len(self.__packages) > 0:
                # clone the list
                packages = []
                for pack in self.__packages:
                    packages.append(pack)
                return packages

    def delete_fragment(self, index: int) -> bool:
        with self.__lock:
            total = len(self.__packages)
            count = total
            for i in range(total):
                if self.__packages[i].head.index == index:
                    # got it!
                    self.__packages.pop(i)
                    count -= 1
                    break
            if count == 0:
                # all fragments sent, remove this task
                return True
            elif count < total:
                # update expired time
                self.__expired = time.time() + self.EXPIRES


"""
    Memory Cache
    ~~~~~~~~~~~~
    
    for departure packages
"""


class DepartureHall:

    def __init__(self):
        super().__init__()
        self.__departures: List[Departure] = []
        self.__map = weakref.WeakValueDictionary()  # TransactionID => Departure
        self.__finished: Dict[bytes, float] = {}    # bytes(TransactionID) => timestamp
        self.__lock = threading.RLock()

    def append(self, pack: Package, source: Optional[tuple], destination: tuple) -> Departure:
        """ Append departure """
        if pack.head.data_type.is_message:
            fragments = Packer.split(package=pack)
        else:
            fragments = [pack]
        task = Departure(packages=fragments, source=source, destination=destination)
        with self.__lock:
            self.__departures.append(task)
            self.__map[task.sn] = task
        return task

    def remove(self, task: Departure):
        """ Remove departure """
        with self.__lock:
            sn = task.sn
            snb = sn.get_bytes()
            self.__departures.remove(task)
            self.__map.pop(sn, None)
            self.__finished[snb] = time.time()

    def next(self) -> Optional[Departure]:
        """ Next expired departure """
        now = time.time()
        with self.__lock:
            for task in self.__departures:
                if task.is_expired(now=now):
                    # got it
                    return task

    def delete_fragment(self, sn: TransactionID, index: int):
        """
        Delete fragment

        :param sn:     transaction ID
        :param index:  fragment index
        """
        with self.__lock:
            snb = sn.get_bytes()
            # check whether this task has already finished
            timestamp = self.__finished.get(snb)
            if timestamp is None or timestamp == 0:
                # check departure
                task = self.__map.get(sn)
                if task is not None:
                    # assert isinstance(task, Departure)
                    if task.delete_fragment(index=index):
                        # all fragments sent, remove this task
                        self.__departures.remove(task)
                        self.__map.pop(sn, None)
                        # mark finished time
                        self.__finished[snb] = time.time()
