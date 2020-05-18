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

from abc import ABC, abstractmethod
from typing import Union, Optional

from udp import Package, Command, Message


class Delegate(ABC):

    @abstractmethod
    def send(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
        """
        Send data to destination address

        :param data:        data package to send
        :param destination: remote address
        :param source:      local address or port number
        :return: -1 on error
        """
        raise NotImplemented


class Task:

    def __init__(self, pack: Union[Package, list], destination: tuple, source: Union[tuple, int]=0):
        super().__init__()
        self.pack = pack
        self.destination = destination
        self.source = source
        self.max_retries = 5


class Peer(ABC):

    def __init__(self):
        super().__init__()
        self.delegate: Delegate = None
        # waiting list for responding
        self.__sent_window = []  # tasks

    #
    #   Sending
    #
    def waiting(self, pack: Union[Package, list], destination: tuple, source: Union[tuple, int]=0) -> Task:
        task = Task(pack=pack, destination=destination, source=source)
        self.__sent_window.append(task)
        return task

    def send(self, task: Task) -> Optional[Task]:
        if task.max_retries > 0:
            task.max_retries -= 1
        else:
            return None
        # treat the task as a bundle of packages
        if isinstance(task.pack, Package):
            pack = [task.pack]
        else:
            assert isinstance(task.pack, list), 'pack error: %s' % task.pack
            pack = task.pack
        for item in pack:
            res = self.delegate.send(data=item.data, destination=task.destination, source=task.source)
            if res < 0:
                raise IOError('failed to resend task (%d packages) to: %s' % (len(pack), task.destination))
        return task

    def move_window(self) -> bool:
        if len(self.__sent_window) == 0:
            return False
        # get the first task in the window
        task = self.__sent_window.pop(0)
        task = self.send(task=task)
        if task is not None:
            # the task is resent, push back to waiting list
            self.__sent_window.append(task)
        return True

    def send_command(self, data: bytes, destination: tuple, source: Union[tuple, int] = None):
        pack = Package.new(data_type=Command, body=data)
        task = self.waiting(pack=pack, destination=destination, source=source)
        self.send(task=task)

    def send_message(self, data: bytes, destination: tuple, source: Union[tuple, int] = None):
        pack = Package.new(data_type=Message, body=data)
        # check body length
        if len(data) > Package.MAX_BODY_LEN:
            pack = Package.split(package=pack)
        task = self.waiting(pack=pack, destination=destination, source=source)
        self.send(task=task)

    #
    #   Received
    #
    def handle(self, data: bytes, source: tuple, destination: tuple):
        """
        Handle received data from source address

        :param data:        data package received
        :param source:      remote address
        :param destination: local address
        """
        raise NotImplemented
