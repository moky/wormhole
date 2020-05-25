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

import threading
import time
from weakref import WeakSet
from abc import ABC, abstractmethod
from typing import Optional, Union

from .connection import Socket, Connection

"""
    Topology:

                        +---------------+
                        |      APP      |
                        +---------------+
                            |       A
                            |       |  (filter)
                            V       |
        +-----------------------------------------------+
        |                                               |
        |     +----------+     HUB     +----------+     |
        |     |  socket  |             |  socket  |     |
        +-----+----------+-------------+----------+-----+
                 |    A                   |  |  A
                 |    |   (connections)   |  |  |
                 |    |                   |  |  |
        ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
        ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
                 |    |                   |  |  |
                 V    |                   V  V  |
"""


class HubFilter(ABC):

    @abstractmethod
    def matched(self, data: bytes, source: tuple, destination: tuple) -> bool:
        """
        Check
        :param data:
        :param source:
        :param destination:
        :return:
        """
        pass


class HubListener(ABC):

    @property
    def filter(self) -> Optional[HubFilter]:
        return None

    @abstractmethod
    def received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        """
        New data package arrived

        :param data:        UDP data received
        :param source:      remote ip and port
        :param destination: local ip and port
        :return: response to the source address
        """
        raise NotImplemented


class Hub(threading.Thread):

    def __init__(self):
        super().__init__()
        self.running = True
        self.__sockets = []
        self.__listeners = WeakSet()
        self.__listeners_lock = threading.Lock()

    def add_listener(self, listener: HubListener):
        with self.__listeners_lock:
            assert listener not in self.__listeners, 'listener already added: %s' % listener
            self.__listeners.add(listener)

    def remove_listener(self, listener: HubListener):
        with self.__listeners_lock:
            assert listener in self.__listeners, 'listener not exists: %s' % listener
            self.__listeners.remove(listener)

    def get_socket(self, source: Union[tuple, int] = None) -> Optional[Socket]:
        if source is None:
            return self.__sockets[0]
        elif isinstance(source, int):
            source = ('0.0.0.0', source)
        for sock in self.__sockets:
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            if sock.local_address == source:
                # already exists
                return sock

    @staticmethod
    def _create_socket(host: str, port: int) -> Optional[Socket]:
        return Socket(host=host, port=port)

    def open(self, port: int, host: str = '0.0.0.0'):
        """ create a socket on this port """
        address = (host, port)
        sock = self.get_socket(source=address)
        if sock is None:
            sock = self._create_socket(host=host, port=port)
            sock.start()
            self.__sockets.append(sock)

    def close(self, port: int, host: str = '0.0.0.0') -> bool:
        """ remove the socket on this port """
        count = 0
        address = (host, port)
        while True:
            sock = self.get_socket(source=address)
            if sock is None:
                break
            sock.close()
            self.__sockets.remove(sock)
            count += 1
        return count > 0

    def stop(self):
        self.running = False
        # close all sockets
        pos = len(self.__sockets)
        while pos > 0:
            pos -= 1
            sock = self.__sockets[pos]
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            sock.stop()

    def connect(self, destination: tuple, source: Union[tuple, int] = None) -> bool:
        sock = self.get_socket(source=source)
        if sock is not None:
            sock.connect(remote_address=destination)
            return True

    def disconnect(self, destination: tuple, source: Union[tuple, int] = None) -> bool:
        sock = self.get_socket(source=source)
        if sock is not None:
            sock.disconnect(remote_address=destination)
            return True

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        """
        Send data from source address(port) to destination address

        :param data:        data package
        :param destination: remote address
        :param source:      local address
        :return:
        """
        sock = None
        assert len(self.__sockets) > 0, 'sockets empty'
        if source is None:
            # any socket
            sock = self.__sockets[0]
        elif isinstance(source, tuple):
            # get socket by local address
            for item in self.__sockets:
                assert isinstance(item, Socket), 'socket error: %s' % item
                if item.local_address == source:
                    sock = item
                    break
        else:
            # get socket by local port
            assert isinstance(source, int), 'source port error: %s' % source
            for item in self.__sockets:
                assert isinstance(item, Socket), 'socket error: %s' % item
                if item.local_address[1] == source:
                    sock = item
                    break
        assert isinstance(sock, Socket), 'no socket (%d) matched: %s' % (len(self.__sockets), source)
        return sock.send(data=data, remote_address=destination)

    def receive(self, timeout: Optional[float]=None) -> (bytes, (str, int), (str, int)):
        """
        Block to receive data

        :return: received data, source address(remote), destination address(local)
        """
        now = time.time()
        if timeout is None:
            timeout = now + 31558150  # 3600 * 24 * 365.25636 (365d 6h 9m 10s)
        else:
            timeout = now + timeout
        while now <= timeout:
            data, source, destination = self.__receive()
            if data is None:
                time.sleep(0.1)
                now = time.time()
            else:
                return data, source, destination
        return None, None, None

    def __receive(self) -> (bytes, (str, int), (str, int)):
        for sock in self.__sockets:
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            data, remote = sock.receive()
            if data is not None:
                # got one
                return data, remote, sock.local_address
        return None, None, None

    def __dispatch(self, data: bytes, source: tuple, destination: tuple) -> list:
        responses = []
        with self.__listeners_lock:
            for listener in self.__listeners:
                assert isinstance(listener, HubListener), 'listener error: %s' % listener
                f = listener.filter
                if f and not f.matched(data=data, source=source, destination=destination):
                    continue
                res = listener.received(data=data, source=source, destination=destination)
                if res is None:
                    continue
                responses.append(res)
        return responses

    def run(self):
        last_time = time.time() + Connection.EXPIRES
        while self.running:
            try:
                # try to receive data
                data, source, destination = self.__receive()
                if data is None:
                    # received nothing, have a rest
                    time.sleep(0.1)
                else:
                    # dispatch data and got responses
                    responses = self.__dispatch(data=data, source=source, destination=destination)
                    for res in responses:
                        self.send(data=res, destination=source, source=destination)
                # check time for next heartbeat
                now = time.time()
                if last_time < now:
                    last_time = now + 2
                    # try heart beat for all connections in all sockets
                    for sock in self.__sockets:
                        assert isinstance(sock, Socket), 'socket error: %s' % sock
                        sock.ping()   # try to keep all connections alive
                        sock.purge()  # remove error connections
            except Exception as error:
                print('run error: %s' % error)
