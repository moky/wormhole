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
from typing import Optional, Set, Dict

from .protocol import TransactionID
from .package import Package
from .packer import Packer


"""
    Data Package Received
    ~~~~~~~~~~~~~~~~~~~~~

    wait for assembling
"""


class Arrival(Packer):

    # Arrival task will be expired after 10 minutes
    # if still not completed.
    EXPIRES = 600  # seconds

    def __init__(self, sn: TransactionID, pages: int, source: tuple, destination: tuple):
        super().__init__(sn=sn, pages=pages)
        self.__source = source
        self.__destination = destination
        self.__expired = 0  # expired time (timestamp in seconds)

    @property
    def source(self) -> tuple:
        return self.__source

    @property
    def destination(self) -> tuple:
        return self.__destination

    def is_expired(self, now: float) -> bool:
        return self.__expired < now

    def insert(self, fragment: Package) -> Optional[Package]:
        if not fragment.head.data_type.is_fragment:
            # message (or command?) no need to assemble
            return fragment
        # message fragment
        pack = super().insert(fragment=fragment)
        if pack is None:
            # update received time
            self.__expired = time.time() + self.EXPIRES
        else:
            # all fragments received, remove this task
            return pack


"""
    Memory Cache
    ~~~~~~~~~~~~
    
    for arrival packages
"""


class ArrivalHall:

    def __init__(self):
        self.__arrivals: Set[Arrival] = set()
        self.__map = weakref.WeakValueDictionary()  # TransactionID => Arrival
        self.__finished: Dict[bytes, float] = {}    # bytes(TransactionID) => timestamp
        self.__lock = threading.RLock()

    def insert(self, fragment: Package, source: tuple, destination: tuple) -> Optional[Package]:
        """
        Insert fragment

        :param fragment:    message fragment
        :param source:      from address
        :param destination: to address
        :return: completed package
        """
        sn = fragment.head.sn
        snb = sn.get_bytes()
        with self.__lock:
            # check whether the task has already finished
            timestamp = self.__finished.get(snb)
            if timestamp is None or timestamp == 0:
                task = self.__map.get(sn)
                if task is None:
                    # new arrival
                    task = Arrival(sn=sn, pages=fragment.head.pages, source=source, destination=destination)
                    self.__arrivals.add(task)
                    self.__map[sn] = task
                # check complete package after inserted
                complete = task.insert(fragment=fragment)
                if complete is not None:
                    # all fragments received, remove this task
                    self.__arrivals.remove(task)
                    self.__map.pop(sn, None)
                    # mark finished time
                    self.__finished[snb] = time.time()
                    return complete

    def purge(self):
        """ Clear expired tasks """
        now = time.time()
        with self.__lock:
            expires = set()
            # get expired tasks
            for task in self.__arrivals:
                if task.is_expired(now=now):
                    expires.add(task)
            # remove expired tasks
            for task in expires:
                self.__arrivals.remove(task)
                self.__map.pop(task.sn, None)
                # mark expired time
                self.__finished[task.sn.get_bytes()] = now
