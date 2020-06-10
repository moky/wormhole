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
from .protocol import Package, TransactionID
from .protocol import Command, CommandRespond
from .protocol import Message, MessageRespond, MessageFragment
from .task import Departure, Arrival, Assemble, Pool, MemPool
from .hub import HubListener


"""
    Topology:

        +-----------------------------------------------+
        |                      APP                      |
        |                (Peer Delegate)                |
        +-----------------------------------------------+
                            |       A
                            |       |
                            V       |
        +---+--------+----------------------------------+
        |   |  Pool  |                                  |        pool:
        |   +--------+         Peer        +--------+   |          -> departures
        |                (Hub Listener)    | Filter |   |          -> arrivals
        +----------------------------------+--------+---+          -> assembling
                            |       A
                            |       |
                            V       |
        +-----------------------------------------------+
        |                      HUB                      |
        +-----------------------------------------------+
"""


class PeerDelegate(ABC):

    # @abstractmethod
    def send_command_success(self, trans_id: TransactionID, destination: tuple, source: tuple):
        """
        Callback for command success.

        :param trans_id:    transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    # @abstractmethod
    def send_command_timeout(self, trans_id: TransactionID, destination: tuple, source: tuple):
        """
        Callback for command failed.

        :param trans_id:    transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    # @abstractmethod
    def send_message_success(self, trans_id: TransactionID, destination: tuple, source: tuple):
        """
        Callback for message success.

        :param trans_id:    transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    # @abstractmethod
    def send_message_timeout(self, trans_id: TransactionID, destination: tuple, source: tuple):
        """
        Callback for message failed.

        :param trans_id:    transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    @abstractmethod
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
        """
        Send data to destination address.

        :param data:        data package to send
        :param destination: remote address
        :param source:      local address or port number
        :return: -1 on error
        """
        raise NotImplemented

    @abstractmethod
    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        """
        Received command data from source address.

        :param cmd:         command data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        """
        Received message data from source address.

        :param msg:         message data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented

    # @abstractmethod
    # noinspection PyUnusedLocal, PyMethodMayBeStatic
    def check_fragment(self, fragment: Package, source: tuple, destination: tuple) -> bool:
        """
        Check message fragment from the source address, if too many incomplete tasks
        from the same address, return False to reject it to avoid 'DDoS' attack.

        :param fragment:    message fragment
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        return True

    # @abstractmethod
    def recycle_fragments(self, fragments: list, source: tuple, destination: tuple):
        """
        Recycle incomplete message fragments from source address.
        (Override for resuming the transaction)

        :param fragments:   fragment packages
        :param source:      remote address
        :param destination: local address
        :return:
        """
        pass


class Peer(threading.Thread, HubListener):

    def __init__(self):
        super().__init__()
        self.running = True
        self.__pool = None
        self.__delegate: weakref.ReferenceType = None

    @property
    def pool(self) -> Pool:
        if self.__pool is None:
            self.__pool = MemPool()
        return self.__pool

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
            task = self.pool.any_departure()
            if task is None:
                # third, if no departure task, remove expired fragments
                assembling = self.pool.discard_fragments()
                for item in assembling:
                    assert isinstance(item, Assemble), 'assemble error: %s' % item
                    self.delegate.recycle_fragments(fragments=item.fragments,
                                                    source=item.source, destination=item.destination)
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
        total = self.pool.arrivals_count()
        done = 0
        while done < total:
            task = self.pool.first_arrival()
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
        data_type = head.data_type
        if data_type == CommandRespond:
            # command response
            trans_id = head.trans_id
            if self.pool.del_departure(response=pack, destination=task.source, source=task.destination):
                # if departure task is deleted, means it's finished
                self.delegate.send_command_success(trans_id=trans_id, destination=task.source, source=task.destination)
            return None
        elif data_type == MessageRespond:
            # message response
            trans_id = head.trans_id
            if self.pool.del_departure(response=pack, destination=task.source, source=task.destination):
                # if departure task is deleted, means it's finished
                self.delegate.send_message_success(trans_id=trans_id, destination=task.source, source=task.destination)
            return None
        elif data_type == Command:
            # handle command
            ok = self.delegate.received_command(cmd=pack.body, source=task.source, destination=task.destination)
        elif data_type == Message:
            # handle message
            ok = self.delegate.received_message(msg=pack.body, source=task.source, destination=task.destination)
        else:
            # handle message fragment
            assert data_type == MessageFragment, 'data type error: %s' % data_type
            ok = self.delegate.check_fragment(fragment=pack, source=task.source, destination=task.destination)
            if ok:
                # assemble fragments
                msg = self.pool.add_fragment(fragment=pack, source=task.source, destination=task.destination)
                if msg is not None:
                    # all fragments received
                    self.delegate.received_message(msg=msg, source=task.source, destination=task.destination)
        # respond to the sender
        if ok:
            self.__respond(pack=pack, remote=task.source, local=task.destination)

    def __respond(self, pack: Package, remote: tuple, local: tuple):
        head = pack.head
        data_type = head.data_type
        if data_type == Command:
            data_type = CommandRespond
            body = b'OK'
        elif data_type == Message:
            data_type = MessageRespond
            body = b'OK'
        elif data_type == MessageFragment:
            data_type = MessageRespond
            body = uint32_to_bytes(head.pages) + uint32_to_bytes(head.offset) + b'OK'
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
        if self.pool.add_departure(task=task):
            # treat the task as a bundle of packages
            packages = task.packages
            for item in packages:
                assert isinstance(item, Package), 'package error: %s' % item
                res = self.delegate.send_data(data=item.data, destination=task.destination, source=task.source)
                if res < 0:
                    raise IOError('failed to resend task (%d packages) to: %s' % (len(packages), task.destination))
            return task
        else:
            # mission failed
            data_type = task.data_type
            trans_id = task.trans_id
            if data_type == Command:
                self.delegate.send_command_timeout(trans_id=trans_id, destination=task.destination, source=task.source)
            elif data_type == Message:
                self.delegate.send_message_timeout(trans_id=trans_id, destination=task.destination, source=task.source)
            else:
                raise AssertionError('data type error: %s' % data_type)

    def send_command(self, pack: Union[Package, bytes],
                     destination: tuple, source: Union[tuple, int]=None) -> Departure:
        if isinstance(pack, bytes):
            pack = Package.new(data_type=Command, body=pack)
        task = Departure(packages=[pack], destination=destination, source=source)
        self.__send(task=task)
        return task

    def send_message(self, pack: Union[Package, bytes],
                     destination: tuple, source: Union[tuple, int]=None) -> Departure:
        if isinstance(pack, bytes):
            pack = Package.new(data_type=Message, body=pack)
        # split packages
        if len(pack.body) <= Package.MAX_BODY_LEN or pack.head.data_type == MessageFragment:
            packages = [pack]
        else:
            packages = Package.split(package=pack)
        task = Departure(packages=packages, destination=destination, source=source)
        self.__send(task=task)
        return task

    #
    #   HubListener
    #
    def received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        task = Arrival(payload=data, source=source, destination=destination)
        self.pool.add_arrival(task=task)
        return None
