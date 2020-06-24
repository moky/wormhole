# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
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
from weakref import WeakSet
from abc import ABC, abstractmethod
from typing import Optional, Union

from .connection import ConnectionStatus, ConnectionDelegate, Connection
from .socket import Socket, DatagramPacket

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
    def data_received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
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


class Cargo:

    def __init__(self, data: bytes, source: tuple, destination: tuple):
        super().__init__()
        self.__data = data
        self.__source = source
        self.__destination = destination

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def source(self) -> tuple:
        return self.__source

    @property
    def destination(self) -> tuple:
        return self.__destination

    @classmethod
    def create(cls, packet: DatagramPacket, socket: Socket):
        return cls(data=packet.data, source=packet.address, destination=socket.local_address)


class Hub(threading.Thread, ConnectionDelegate):

    def __init__(self):
        super().__init__()
        self.running = False
        # sockets
        self.__sockets = set()
        self.__sockets_lock = threading.RLock()
        # listeners
        self.__listeners = WeakSet()
        self.__listeners_lock = threading.Lock()

    #
    #  Listeners
    #

    def add_listener(self, listener: HubListener):
        with self.__listeners_lock:
            assert listener not in self.__listeners, 'listener already added: %s' % listener
            self.__listeners.add(listener)

    def remove_listener(self, listener: HubListener):
        with self.__listeners_lock:
            assert listener in self.__listeners, 'listener not exists: %s' % listener
            self.__listeners.remove(listener)
            return True

    #
    #  Sockets
    #

    def __any_socket(self) -> Optional[Socket]:
        """ get arbitrary socket """
        with self.__sockets_lock:
            for sock in self.__sockets:
                return sock

    def __get_sockets(self, port: int) -> set:
        """ get all sockets bond to this port """
        with self.__sockets_lock:
            sockets = set()
            for sock in self.__sockets:
                assert isinstance(sock, Socket), 'socket error: %s' % sock
                if port == sock.port:
                    sockets.add(sock)
            return sockets

    def __get_socket(self, port: int, host: str=None) -> Optional[Socket]:
        if host is None:
            # get socket by port
            with self.__sockets_lock:
                for sock in self.__sockets:
                    assert isinstance(sock, Socket), 'socket error: %s' % sock
                    if port == sock.port:
                        return sock
        else:
            # get socket by (IP, port)
            with self.__sockets_lock:
                for sock in self.__sockets:
                    assert isinstance(sock, Socket), 'socket error: %s' % sock
                    if port == sock.port and host == sock.host:
                        return sock

    def _create_socket(self, host: str, port: int) -> Socket:
        sock = Socket(host=host, port=port)
        sock.delegate = self
        sock.start()
        return sock

    def open(self, port: int, host: str='0.0.0.0') -> Socket:
        """ create a socket on this port """
        with self.__sockets_lock:
            sock = self.__get_socket(host=host, port=port)
            if sock is None:
                sock = self._create_socket(host=host, port=port)
                self.__sockets.add(sock)
            return sock

    def close(self, port: int, host: str=None) -> set:
        """ remove the socket(s) on this port """
        with self.__sockets_lock:
            closed = set()
            while True:
                sock = self.__get_socket(host=host, port=port)
                if sock is None:
                    break
                sock.close()
                closed.add(sock)
                self.__sockets.remove(sock)
            return closed

    def start(self):
        self.running = True
        super().start()

    def stop(self):
        self.running = False
        # close all sockets
        with self.__sockets_lock:
            for sock in self.__sockets:
                assert isinstance(sock, Socket), 'socket error: %s' % sock
                sock.stop()
            self.__sockets.clear()

    def connect(self, destination: tuple, source: Union[tuple, int]=None) -> Optional[Connection]:
        if source is None:
            # connect from any socket
            sock = self.__any_socket()
        elif isinstance(source, int):
            # connect from the port
            sock = self.__get_socket(port=source)
        else:
            # connect from the address
            sock = self.__get_socket(host=source[0], port=source[1])
        if sock is not None:
            return sock.connect(remote_address=destination)

    def disconnect(self, destination: tuple, source: Union[tuple, int]=None) -> set:
        if source is None:
            # disconnect from all sockets
            with self.__sockets_lock:
                sockets = self.__sockets.copy()
        elif isinstance(source, int):
            # disconnect from sockets on this port
            sockets = self.__get_sockets(port=source)
        else:
            # disconnect from the address
            sockets = set()
            sock = self.__get_socket(host=source[0], port=source[1])
            if sock is not None:
                sockets.add(sock)
        all_removed = set()
        for sock in sockets:
            removed = sock.disconnect(remote_address=destination)
            if len(removed) > 0:
                all_removed = all_removed.union(removed)
        return all_removed

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
        """
        Send data from source address(port) to destination address

        :param data:        data package
        :param destination: remote address
        :param source:      local address
        :return:
        """
        if source is None:
            # connect from any socket
            sock = self.__any_socket()
        elif isinstance(source, int):
            # connect from the port
            sock = self.__get_socket(port=source)
        else:
            # connect from the address
            sock = self.__get_socket(host=source[0], port=source[1])
        if sock is not None:
            return sock.send(data=data, remote_address=destination)

    def __receive_all(self) -> Optional[Cargo]:
        with self.__sockets_lock:
            # receive data from any socket
            return self.__receive_from_sockets(sockets=self.__sockets)

    @staticmethod
    def __receive_from_sockets(sockets) -> Optional[Cargo]:
        for sock in sockets:
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            packet = sock.receive()
            if packet is not None:
                return Cargo.create(packet=packet, socket=sock)

    def __receive(self, host: str=None, port: int=0) -> Optional[Cargo]:
        if port is 0:
            return self.__receive_all()
        if host is None:
            sockets = self.__get_sockets(port=port)
            return self.__receive_from_sockets(sockets=sockets)
        # receive data from appointed socket
        sock = self.__get_socket(host=host, port=port)
        if sock is not None:
            packet = sock.receive()
            if packet is not None:
                return Cargo.create(packet=packet, socket=sock)

    def receive(self, host: str=None, port: int=0, timeout: float=None) -> Optional[Cargo]:
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
            cargo = self.__receive(host=host, port=port)
            if cargo is None:
                time.sleep(0.1)
                now = time.time()
            else:
                return cargo

    def run(self):
        expired = time.time() + Connection.EXPIRES
        while self.running:
            try:
                # try to receive data
                cargo = self.__receive_all()
                if cargo is None:
                    # received nothing, have a rest
                    time.sleep(0.1)
                else:
                    # dispatch data and got responses
                    responses = self.__dispatch(data=cargo.data, source=cargo.source, destination=cargo.destination)
                    for res in responses:
                        self.send(data=res, destination=cargo.source, source=cargo.destination)
                # check time for next heartbeat
                now = time.time()
                if now > expired:
                    expired = now + 2
                    # try heart beat for all connections in all sockets
                    self._heartbeat()
            except Exception as error:
                print('Hub.run error: %s' % error)

    def _heartbeat(self):
        with self.__sockets_lock:
            for sock in self.__sockets:
                assert isinstance(sock, Socket), 'socket error: %s' % sock
                sock.ping()  # try to keep all connections alive
                sock.purge()  # remove error connections

    def __dispatch(self, data: bytes, source: tuple, destination: tuple) -> list:
        responses = []
        with self.__listeners_lock:
            for listener in self.__listeners:
                assert isinstance(listener, HubListener), 'listener error: %s' % listener
                f = listener.filter
                if f is not None and not f.check_data(data=data, source=source, destination=destination):
                    continue
                res = listener.data_received(data=data, source=source, destination=destination)
                if res is None:
                    continue
                responses.append(res)
        return responses

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
        address = connection.local_address
        cargo = self.__receive(host=address[0], port=address[1])
        if cargo is None:
            # assert False
            return False
        # dispatch data and got responses
        responses = self.__dispatch(data=cargo.data, source=cargo.source, destination=cargo.destination)
        for res in responses:
            self.send(data=res, destination=cargo.source, source=cargo.destination)
