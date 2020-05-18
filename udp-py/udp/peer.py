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

import time
from abc import ABC, abstractmethod
from typing import Union, Optional

from .data import uint32_to_bytes
from .protocol import Package
from .protocol import Command, CommandRespond
from .protocol import Message, MessageRespond, MessageFragment
from .task import Departure, Arrival, Pool


class Delegate(ABC):

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

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        """
        Received command data from source address

        :param cmd:         command data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        """
        Received message data from source address

        :param msg:         message data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented


class Peer:

    def __init__(self):
        super().__init__()
        self.delegate: Delegate = None
        self.__pool = Pool()

    def purge_departures(self) -> bool:
        """
        Redo the sending tasks in waiting list

        :return: False on no task
        """
        total = self.__pool.departures_count()
        done = 0
        while done < total:
            task = self.__pool.get_departure()
            if task is None:
                # no task or task not expired
                break
            task = self.__send(task=task)
            if task is not None:
                # push the task back to waiting list for responding or retrying
                self.__pool.add_departure(task)
            done += 1
        return done > 0

    def purge_arrivals(self) -> bool:
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
        return done > 0

    #
    #   Received
    #
    def received(self, data: bytes, source: tuple, destination: tuple) -> Arrival:
        """
        New data package arrived

        :param data:        UDP data received
        :param source:      remote ip and port
        :param destination: local ip and port
        :return:
        """
        return self.__pool.new_arrival(data=data, source=source, destination=destination)

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
            self.delegate.received_command(cmd=body, source=task.source, destination=task.destination)
        elif data_type == Message:
            self.delegate.received_message(msg=body, source=task.source, destination=task.destination)
        else:
            assert data_type == MessageFragment, 'data type error: %s' % data_type
            msg = self.__assemble(fragment=pack, source=task.source, destination=task.destination)
            if msg is not None:
                self.delegate.received_message(msg=msg, source=task.source, destination=task.destination)
        # respond to the sender
        self.__respond(pack=pack, remote=task.source, local=task.destination)

    def __assemble(self, fragment: Package, source: tuple, destination: tuple) -> Optional[bytes]:
        # TODO: assembling fragments
        pass

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
        version = head.version
        sn = head.trans_id
        response = Package.new(data_type=data_type, sn=sn, body=body, version=version)
        # send response directly, don't at this task to waiting list
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
            return task

    def send_command(self, data: bytes, destination: tuple, source: Union[tuple, int]=None):
        pack = Package.new(data_type=Command, body=data)
        task = self.__pool.new_departure(payload=pack, destination=destination, source=source)
        self.__send(task=task)

    def send_message(self, data: bytes, destination: tuple, source: Union[tuple, int]=None):
        pack = Package.new(data_type=Message, body=data)
        # check body length
        if len(data) > Package.MAX_BODY_LEN:
            pack = Package.split(package=pack)
        task = self.__pool.new_departure(payload=pack, destination=destination, source=source)
        self.__send(task=task)
