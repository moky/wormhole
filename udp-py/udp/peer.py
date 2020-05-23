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
import weakref
from abc import ABC, abstractmethod
from typing import Union, Optional

from .data import uint32_to_bytes
from .protocol import Package
from .protocol import Command, CommandRespond
from .protocol import Message, MessageRespond, MessageFragment
from .task import Departure, Arrival, Pool
from .hub import HubListener


class PeerDelegate(ABC):

    @abstractmethod
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
        """
        Send data to destination address

        :param data:        data package to send
        :param destination: remote address
        :param source:      local address or port number
        :return: -1 on error
        """
        raise NotImplemented

    @abstractmethod
    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        """
        Received command data from source address

        :param cmd:         command data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        """
        Received message data from source address

        :param msg:         message data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented


class Peer(threading.Thread, HubListener):

    def __init__(self):
        super().__init__()
        self.running = True
        self.__pool = Pool()
        self.__delegate: weakref.ReferenceType = None

    @property
    def delegate(self) -> Optional[PeerDelegate]:
        if self.__delegate is not None:
            return self.__delegate()

    @delegate.setter
    def delegate(self, value: Optional[PeerDelegate]):
        self.__delegate = weakref.ref(value)

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            # first, process all arrivals
            done = self.__clean_arrivals()
            # second, get one departure task
            task = self.__pool.get_departure()
            if task is None:
                # if no departure task, remove expired fragments
                self.__pool.discard_fragments()
                if done == 0:
                    # all jobs done, have a rest. ^_^
                    time.sleep(0.1)
            else:
                # redo this departure task
                self.__send(task=task)

    def __clean_arrivals(self) -> int:
        """
        Process the received packages in waiting list

        :return: False on no data
        """
        total = self.__pool.arrivals_count()
        done = 0
        while done < total:
            task = self.__pool.get_arrival()
            if task is None:
                # no data now
                break
            self.__handle(task=task)
            done += 1
        return done

    def __handle(self, task: Arrival):
        pack = Package.parse(data=task.payload)
        assert pack is not None, 'package error: %s' % task.payload
        head = pack.head
        body = pack.body
        data_type = head.data_type
        if data_type == CommandRespond or data_type == MessageRespond:
            self.__pool.del_departure(response=pack)
            return None
        elif data_type == Command:
            ack = self.delegate.received_command(cmd=body, source=task.source, destination=task.destination)
        elif data_type == Message:
            ack = self.delegate.received_message(msg=body, source=task.source, destination=task.destination)
        else:
            assert data_type == MessageFragment, 'data type error: %s' % data_type
            # assemble fragments
            msg = self.__pool.add_fragment(fragment=pack)
            if msg is None:
                ack = True
            else:
                # all fragments received
                ack = self.delegate.received_message(msg=msg, source=task.source, destination=task.destination)
        # respond to the sender
        if ack:
            self.__respond(pack=pack, remote=task.source, local=task.destination)

    def __respond(self, pack: Package, remote: tuple, local: tuple):
        head = pack.head
        data_type = head.data_type
        if data_type == Command:
            data_type = CommandRespond
            body = b''
        elif data_type == Message:
            data_type = MessageRespond
            body = b''
        elif data_type == MessageFragment:
            data_type = MessageRespond
            body = uint32_to_bytes(head.pages) + uint32_to_bytes(head.offset)
        else:
            raise TypeError('data type error: %s' % data_type)
        sn = head.trans_id
        response = Package.new(data_type=data_type, sn=sn, body=body)
        # send response directly, don't add this task to waiting list
        res = self.delegate.send_data(data=response.data, destination=remote, source=local)
        if res < 0:
            raise IOError('failed to respond %s: %s' % (data_type, remote))

    #
    #   Sending
    #
    def __send(self, task: Departure) -> Optional[Departure]:
        # treat the task as a bundle of packages
        if isinstance(task.payload, Package):
            pack = [task.payload]
        else:
            assert isinstance(task.payload, list), 'pack error: %s' % task.payload
            pack = task.payload
        for item in pack:
            res = self.delegate.send_data(data=item.data, destination=task.destination, source=task.source)
            if res < 0:
                raise IOError('failed to resend task (%d packages) to: %s' % (len(pack), task.destination))
        if task.max_retries > 0:
            task.last_time = time.time()
            task.max_retries -= 1
            self.__pool.add_departure(task=task)
            return task

    def send_command(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> Departure:
        pack = Package.new(data_type=Command, body=data)
        task = Departure(payload=pack, destination=destination, source=source)
        self.__send(task=task)
        return task

    def send_message(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> Departure:
        pack = Package.new(data_type=Message, body=data)
        # check body length
        if len(data) > Package.MAX_BODY_LEN:
            pack = Package.split(package=pack)
        task = Departure(payload=pack, destination=destination, source=source)
        self.__send(task=task)
        return task

    #
    #   HubListener
    #
    def received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        task = Arrival(payload=data, source=source, destination=destination)
        self.__pool.add_arrival(task=task)
        return None
