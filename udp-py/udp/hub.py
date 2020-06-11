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

from .connection import Socket, Connection, ConnectionDelegate, ConnectionStatus

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
    def check_data(self, data: bytes, source: tuple, destination: tuple) -> bool:
        """
        Check for observing message data

        :param data:        UDP data received
        :param source:      remote IP and port
        :param destination: local IP and port
        :return: False to ignore it
        """
        raise NotImplemented

    # @abstractmethod
    def check_connection(self, connection: Connection) -> bool:
        """
        Check for observing connection

        :param connection:
        :return: False to ignore it
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
        :param source:      remote IP and port
        :param destination: local IP and port
        :return: response to the source address
        """
        raise NotImplemented

    # @abstractmethod
    def status_changed(self, connection: Connection, old_status: ConnectionStatus, new_status: ConnectionStatus):
        """
        Status changed

        :param connection:
        :param old_status:
        :param new_status:
        """
        pass


class Hub(threading.Thread, ConnectionDelegate):

    def __init__(self):
        super().__init__()
        self.running = False
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

    def __get_socket(self, host: str='0.0.0.0', port: int=0) -> Optional[Socket]:
        if port is 0:
            # any socket
            assert host == '0.0.0.0', 'failed to get socket (%s:%d)' % (host, port)
            assert len(self.__sockets) > 0, 'sockets empty'
            return self.__sockets[0]
        # 1. check address exactly
        address = (host, port)
        for sock in self.__sockets:
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            if sock.local_address == address:
                return sock
        if host == '0.0.0.0':
            # 2. check with port
            for sock in self.__sockets:
                assert isinstance(sock, Socket), 'socket error: %s' % sock
                if sock.local_address[1] == port:
                    return sock
        else:
            # 3. check sockets binding to '0.0.0.0'
            for sock in self.__sockets:
                assert isinstance(sock, Socket), 'socket error: %s' % sock
                if sock.local_address[1] == port and sock.local_address[0] == '0.0.0.0':
                    return sock

    def _get_socket(self, source: Union[tuple, int]) -> Optional[Socket]:
        if source is None:
            # any socket
            return self.__get_socket()
        elif isinstance(source, int):
            # get socket by port
            return self.__get_socket(port=source)
        else:
            assert isinstance(source, tuple) and len(source) == 2, 'source address error: %s' % str(source)
            # get socket by address
            return self.__get_socket(host=source[0], port=source[1])

    # noinspection PyMethodMayBeStatic
    def _create_socket(self, host: str, port: int) -> Optional[Socket]:
        sock = Socket(host=host, port=port)
        sock.connection_delegate = self
        return sock

    def open(self, port: int, host: str='0.0.0.0'):
        """ create a socket on this port """
        sock = self.__get_socket(host=host, port=port)
        if sock is None:
            sock = self._create_socket(host=host, port=port)
            sock.start()
            self.__sockets.append(sock)

    def close(self, port: int, host: str='0.0.0.0') -> bool:
        """ remove the socket on this port """
        count = 0
        while True:
            sock = self.__get_socket(host=host, port=port)
            if sock is None:
                break
            sock.close()
            self.__sockets.remove(sock)
            count += 1
        return count > 0

    def start(self):
        self.running = True
        super().start()

    def stop(self):
        self.running = False
        # close all sockets
        pos = len(self.__sockets)
        while pos > 0:
            pos -= 1
            sock = self.__sockets[pos]
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            sock.stop()

    def connect(self, destination: tuple, source: Union[tuple, int]=None) -> Optional[Connection]:
        sock = self._get_socket(source=source)
        if sock is not None:
            return sock.connect(remote_address=destination)

    def disconnect(self, destination: tuple, source: Union[tuple, int]=None) -> bool:
        sock = self._get_socket(source=source)
        if sock is not None:
            sock.disconnect(remote_address=destination)
            return True

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
        """
        Send data from source address(port) to destination address

        :param data:        data package
        :param destination: remote address
        :param source:      local address
        :return:
        """
        sock = self._get_socket(source=source)
        if sock is not None:
            return sock.send(data=data, remote_address=destination)

    def receive(self, source: Union[tuple, int]=None, timeout: Optional[float]=None) -> (bytes, (str, int), (str, int)):
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
            data, source, destination = self.__receive(source=source)
            if data is None:
                time.sleep(0.1)
                now = time.time()
            else:
                return data, source, destination
        return None, None, None

    def __receive(self, source: Union[tuple, int]=None) -> (bytes, (str, int), (str, int)):
        if source is None:
            # receive data from any socket
            for sock in self.__sockets:
                assert isinstance(sock, Socket), 'socket error: %s' % sock
                data, remote = sock.receive()
                if data is not None:
                    # got one
                    return data, remote, sock.local_address
        else:
            # receive data from appointed socket
            sock = self._get_socket(source=source)
            data, remote = sock.receive()
            if data is not None:
                # got it
                return data, remote, sock.local_address
        return None, None, None

    def __dispatch(self, data: bytes, source: tuple, destination: tuple) -> list:
        responses = []
        with self.__listeners_lock:
            for listener in self.__listeners:
                assert isinstance(listener, HubListener), 'listener error: %s' % listener
                f = listener.filter
                if f is not None and not f.check_data(data=data, source=source, destination=destination):
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

    #
    #   ConnectionDelegate
    #
    def connection_status_changed(self, connection: Connection,
                                  old_status: ConnectionStatus, new_status: ConnectionStatus):
        with self.__listeners_lock:
            for listener in self.__listeners:
                assert isinstance(listener, HubListener), 'listener error: %s' % listener
                f = listener.filter
                if f is not None and not f.check_connection(connection=connection):
                    continue
                listener.status_changed(connection=connection, old_status=old_status, new_status=new_status)

    def connection_received_data(self, connection: Connection):
        if self.running:
            # process by run()
            return True
        data, source, destination = self.__receive(source=connection.local_address)
        if data is None:
            # assert False
            return False
        # dispatch data and got responses
        responses = self.__dispatch(data=data, source=source, destination=destination)
        for res in responses:
            self.send(data=res, destination=source, source=destination)
