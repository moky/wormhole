# -*- coding: utf-8 -*-
#
#   IPX: Inter-Process eXchange
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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

from abc import ABC, abstractmethod
from typing import Any, Optional

from .shm import SharedMemoryController
from .shm import DefaultSharedMemoryController


class Arrow(ABC):
    """ Half-duplex Pipe from A to B """

    @abstractmethod
    def send(self, obj: Optional[Any]) -> int:
        """
        Called by A to send an object from A to B, -1 on failed

        :param obj: any object (dict, list, str, int, float, ...)
        :return: how many stranded passengers; 0 on all sent; -1 on full (failed)
        """
        raise NotImplemented

    @abstractmethod
    def receive(self) -> Optional[Any]:
        """
        Called by B to receive something from A to B

        :return: None on received nothing
        """
        raise NotImplemented


class SharedMemoryArrow(Arrow):
    """ Arrow goes through Shared Memory """

    def __init__(self, controller: SharedMemoryController, max_arrivals: int = 65536, max_departures: int = 65536):
        super().__init__()
        self.__ctrl = controller
        self.__max_arrivals = max_arrivals
        self.__max_departures = max_departures
        # memory caches
        self.__arrivals = []
        self.__departures = []

    @property
    def controller(self) -> SharedMemoryController:
        return self.__ctrl

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        ctrl = self.controller
        arrivals = len(self.__arrivals)
        departures = len(self.__departures)
        return '<%s arrivals=%d departures=%d>%s</%s module="%s">' % (cname, arrivals, departures, ctrl, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        ctrl = self.controller
        arrivals = len(self.__arrivals)
        departures = len(self.__departures)
        return '<%s arrivals=%d departures=%d>%s</%s module="%s">' % (cname, arrivals, departures, ctrl, cname, mod)

    # Override
    def send(self, obj: Optional[Any]) -> int:
        empty = True
        # 1. resent delay objects first
        delays = self.__departures.copy()
        for item in delays:
            if self.controller.push(obj=item):
                # sent, remove from the queue
                self.__departures.remove(item)
            else:
                # shared memory is full, delay list not empty
                empty = False
                break
        # 2. send this obj when delay list empty
        if empty and self.controller.push(obj=obj):
            # success
            return 0
        # 3. check and append to delay queue
        count = len(self.__departures)
        if obj is None:
            return count
        elif count < self.__max_departures:
            # put it into the queue
            self.__departures.append(obj)
            return count + 1
        else:
            # the queue is full
            return -1

    # Override
    def receive(self) -> Optional[Any]:
        count = len(self.__arrivals)
        while count < self.__max_arrivals:
            # receive new objects from the pool
            obj = self.controller.shift()
            if obj is None:
                break
            else:
                # append to waiting queue
                self.__arrivals.append(obj)
                count += 1
        if count > 0:
            return self.__arrivals.pop(0)

    def detach(self):
        self.controller.detach()

    def destroy(self):
        self.controller.destroy()

    @classmethod
    def new(cls, size: int, name: str):
        controller = DefaultSharedMemoryController.new(size=size, name=name)
        return cls(controller=controller)
