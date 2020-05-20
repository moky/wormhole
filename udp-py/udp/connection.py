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

import socket
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Union

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


class Connection:

    EXPIRES = 28  # seconds

    def __init__(self, remote_host: str, remote_port: int):
        super().__init__()
        self.__host = remote_host
        self.__port = remote_port
        self.__expired = 0

    @property
    def host(self) -> str:
        """ remote host """
        return self.__host

    @property
    def port(self) -> int:
        """ remote port """
        return self.__port

    @property
    def is_expired(self):
        """ long time no see """
        return time.time() > self.__expired

    def update_time(self):
        """ update last communicate time """
        self.__expired = time.time() + self.EXPIRES


class Cargo:

    def __init__(self, data: bytes, source: tuple):
        super().__init__()
        self.data = data
        self.source = source


class Socket(threading.Thread):

    def __init__(self, port: int, host: str='0.0.0.0'):
        super().__init__()
        self.running = True
        self.__local_address = (host, port)
        # create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(self.__local_address)
        self.__socket = sock
        # connection list
        self.__connections = []
        self.__connections_lock = threading.Lock()
        # received packages
        self.__cargoes = []
        self.__cargoes_lock = threading.Lock()

    @property
    def local_address(self) -> (str, int):
        return self.__local_address

    def settimeout(self, timeout: Optional[float]):
        self.__socket.settimeout(timeout)

    def close(self):
        self.running = False
        self.__socket.close()

    def connect(self, remote_host: str, remote_port: int):
        """ add remote address to keep connected with heartbeat """
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.host == remote_host and conn.port == remote_port:
                    # already connected
                    return
            conn = Connection(remote_host=remote_host, remote_port=remote_port)
            self.__connections.append(conn)

    def disconnect(self, remote_host: str, remote_port: int):
        """ remove remote address from heartbeat tasks """
        with self.__connections_lock:
            pos = len(self.__connections)
            while pos > 0:
                pos -= 1
                conn = self.__connections[pos]
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.host == remote_host and conn.port == remote_port:
                    # got one
                    self.__connections.pop(pos)

    def __expired_connection(self) -> Optional[Connection]:
        """ get any expired connection """
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.is_expired:
                    return conn

    def __refresh(self, remote_host: str, remote_port: int) -> bool:
        """ update connection's expired time """
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.host == remote_host and conn.port == remote_port:
                    # refresh time
                    conn.update_time()
                    return True

    def ping(self):
        """ send heartbeat to all expired connections """
        while True:
            conn = self.__expired_connection()
            if conn is None:
                # no more expired connection
                break
            self.send(data=b'PING', remote_host=conn.host, remote_port=conn.port)

    def send(self, data: bytes, remote_host: str, remote_port: int) -> int:
        """
        Send data to remote address

        :param data:
        :param remote_host:
        :param remote_port:
        :return: how many bytes have been sent
        """
        try:
            res = self.__socket.sendto(data, (remote_host, remote_port))
            if res == len(data):
                self.__refresh(remote_host=remote_host, remote_port=remote_port)
            return res
        except socket.error as error:
            print('Failed to send data: %s' % error)
            return -1

    def __receive(self, buffer_size: int=2048) -> (bytes, (str, int)):
        try:
            data, address = self.__socket.recvfrom(buffer_size)
            if data is not None:
                assert len(address) == 2, 'remote address error: %s, data length: %d' % (address, len(data))
                self.__refresh(remote_host=address[0], remote_port=address[1])
            return data, address
        except socket.error as error:
            print('Failed to receive data: %s' % error)
            return None, None

    def receive(self) -> (bytes, (str, int)):
        """
        Get received data package from buffer, non-blocked

        :return: received data and source address
        """
        with self.__cargoes_lock:
            if len(self.__cargoes) > 0:
                cargo = self.__cargoes.pop(0)
                assert isinstance(cargo, Cargo), 'cargo error: %s' % cargo
                return cargo.data, cargo.source
        return None, None

    def run(self):
        while self.running:
            try:
                data, address = self.__receive()
                if data is None:
                    # receive nothing
                    time.sleep(0.1)
                elif len(data) == 4:
                    # heartbeat
                    if data == b'PING':
                        # respond heartbeat
                        self.send(data=b'PONG', remote_host=address[0], remote_port=address[1])
                    else:
                        # ignore it
                        assert data == b'PONG', 'drop package: %s' % data
                else:
                    # cache the data received
                    with self.__cargoes_lock:
                        self.__cargoes.append(Cargo(data=data, source=address))
            except Exception as error:
                print('socket error: %s' % error)


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
        self.__listeners = []

    def add_listener(self, listener: HubListener):
        assert listener not in self.__listeners, 'listener already added: %s' % listener
        self.__listeners.append(listener)

    def remove_listener(self, listener: HubListener):
        assert listener in self.__listeners, 'listener not exists: %s' % listener
        self.__listeners.remove(listener)

    def open(self, port: int, host: str='0.0.0.0'):
        """ create a socket on this port """
        address = (host, port)
        for sock in self.__sockets:
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            if sock.local_address == address:
                # already exists
                return False
        sock = Socket(host=host, port=port)
        sock.start()
        self.__sockets.append(sock)
        return True

    def close(self, port: int, host: str='0.0.0.0'):
        """ remove the socket on this port """
        address = (host, port)
        pos = len(self.__sockets)
        while pos > 0:
            pos -= 1
            sock = self.__sockets[pos]
            assert isinstance(sock, Socket), 'socket error: %s' % sock
            if sock.local_address == address:
                # close & remove
                sock.close()
                self.__sockets.pop(pos)

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
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
        return sock.send(data=data, remote_host=destination[0], remote_port=destination[1])

    def receive(self) -> (bytes, (str, int), (str, int)):
        """
        Block to receive data

        :return: received data, source address(remote), destination address(local)
        """
        while True:
            data, source, destination = self.__receive()
            if data is None:
                time.sleep(0.1)
            else:
                return data, source, destination

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
                        sock.ping()
            except Exception as error:
                print('run error: %s' % error)
