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
    def send(self, obj: Any) -> int:
        """
        Called by A to send an object from A to B

        :param obj: any object (dict, list, str, int, float, ...)
        :return: how many stranded passengers； 0 on all sent
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

    MAX_ARRIVALS = 65536
    MAX_DEPARTURES = 65536

    def __init__(self, controller: SharedMemoryController):
        super().__init__()
        self.__ctrl = controller
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
    def send(self, obj: Any) -> int:
        empty = True
        # resent delay objects first
        delays = self.__departures.copy()
        for item in delays:
            if self.controller.push(obj=item):
                # sent, remove from the queue
                self.__departures.remove(item)
            else:
                # shared memory is full, delay list not empty
                empty = False
                break
        # send this obj when delay list empty
        if empty and self.controller.push(obj=obj):
            return 0
        # failed, put it into the queue
        _, _, count = self._push_departure(obj=obj)
        return count

    # Override
    def receive(self) -> Optional[Any]:
        # receive new objects from the pool
        obj = self.controller.shift()
        while obj is not None and self.__receive_arrival(obj=obj):
            obj = self.controller.shift()
        _, obj = self._push_arrival(obj=obj)
        return obj

    def _push_departure(self, obj: Optional[Any]) -> (Optional[Any], Optional[Any], int):
        """ Check the departure hall,
            if it is full, remove two passengers from the front

        :return: discard passengers and new queue length
        """
        if obj is not None:
            self.__departures.append(obj)
        count = len(self.__departures)
        if count > self.MAX_DEPARTURES:
            print('[IPC] pool control, departures: %d' % count)
            return self.__departures.pop(0), self.__departures.pop(0), count - 2
        else:
            return None, None, count

    def __receive_arrival(self, obj: Any) -> bool:
        count = len(self.__arrivals)
        if count < self.MAX_ARRIVALS:
            self.__arrivals.append(obj)
            return True

    def _push_arrival(self, obj: Optional[Any]) -> (Optional[Any], Optional[Any]):
        """ Check the arrival hall,
            if it is full, remove two passengers from the front

        :param obj: new passenger
        :return: dequeue passenger(s)
        """
        if obj is not None:
            self.__arrivals.append(obj)
        count = len(self.__arrivals)
        if count > self.MAX_ARRIVALS:
            print('[IPC] pool control, arrivals: %d' % count)
            return self.__arrivals.pop(0), self.__arrivals.pop(0)
        elif count > 0:
            return None, self.__arrivals.pop(0)
        else:
            return None, None

    def detach(self):
        self.controller.detach()

    def destroy(self):
        self.controller.destroy()

    @classmethod
    def new(cls, size: int, name: str):
        controller = DefaultSharedMemoryController.new(size=size, name=name)
        return cls(controller=controller)
