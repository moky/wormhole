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
from enum import IntEnum
from typing import Optional


class ConnectionStatus(IntEnum):

    NotConnect = 0
    Connecting = 1
    Connected = 2


class Connection:

    EXPIRES = 28  # seconds

    def __init__(self, remote_host: str, remote_port: int):
        super().__init__()
        self.__host = remote_host
        self.__port = remote_port
        # connecting time
        self.__send_expired = 0
        self.__receive_expired = 0

    @property
    def host(self) -> str:
        """ remote host """
        return self.__host

    @property
    def port(self) -> int:
        """ remote port """
        return self.__port

    @property
    def status(self) -> ConnectionStatus:
        now = time.time()
        if now < self.__receive_expired:
            return ConnectionStatus.Connected
        elif now < self.__send_expired:
            return ConnectionStatus.Connecting
        else:
            return ConnectionStatus.NotConnect

    def update_sent_time(self):
        """ update last send time """
        self.__send_expired = time.time() + self.EXPIRES

    def update_received_time(self):
        """ update last send time """
        self.__receive_expired = time.time() + self.EXPIRES


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
        sock = self._create_socket()
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

    @staticmethod
    def _create_socket() -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock

    def settimeout(self, timeout: Optional[float]):
        self.__socket.settimeout(timeout)

    def get_connection(self, remote_host: str, remote_port: int) -> Optional[Connection]:
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.host == remote_host and conn.port == remote_port:
                    # got it
                    return conn

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
                if conn.status == ConnectionStatus.NotConnect:
                    return conn

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
            assert res == len(data), 'send failed: %d, %d' % (res, len(data))
            # update connection's expired time
            with self.__connections_lock:
                for conn in self.__connections:
                    assert isinstance(conn, Connection), 'connection error: %s' % conn
                    if conn.host == remote_host and conn.port == remote_port:
                        # refresh time
                        conn.update_sent_time()
            return res
        except socket.error as error:
            print('Failed to send data: %s' % error)
            return -1

    def __receive(self, buffer_size: int=2048) -> (bytes, (str, int)):
        try:
            data, address = self.__socket.recvfrom(buffer_size)
            if data is not None:
                assert len(address) == 2, 'remote address error: %s, data length: %d' % (address, len(data))
                # update connection's expired time
                with self.__connections_lock:
                    remote_host = address[0]
                    remote_port = address[1]
                    for conn in self.__connections:
                        assert isinstance(conn, Connection), 'connection error: %s' % conn
                        if conn.host == remote_host and conn.port == remote_port:
                            # refresh time
                            conn.update_received_time()
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
                    continue
                if len(data) == 4:
                    # check heartbeat
                    if data == b'PING':
                        # respond heartbeat
                        self.send(data=b'PONG', remote_host=address[0], remote_port=address[1])
                        continue
                    elif data == b'PONG':
                        # ignore it
                        continue
                # cache the data received
                with self.__cargoes_lock:
                    self.__cargoes.append(Cargo(data=data, source=address))
            except Exception as error:
                print('socket error: %s' % error)

    def close(self):
        self.running = False
        self.__socket.close()

    def stop(self):
        self.close()
