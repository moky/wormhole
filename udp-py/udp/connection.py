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
from typing import Optional

from .delegate import SocketDelegate


class Connection:

    EXPIRES = 28  # seconds

    def __init__(self, remote_host: str, remote_port: int):
        super().__init__()
        self.__host = remote_host
        self.__port = remote_port
        self.__expired = 0

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port

    @property
    def is_expired(self):
        return time.time() > self.__expired

    def update_expired_time(self):
        self.__expired = time.time() + self.EXPIRES


class Socket(threading.Thread):

    def __init__(self, host: str='0.0.0.0', port: int=9527):
        super().__init__()
        self.__local_address = (host, port)
        self.delegate: SocketDelegate = None
        # create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(self.__local_address)
        self.__socket = sock
        self.running = True
        # connection list
        self.__connections = []
        self.__connections_lock = threading.Lock()
        # background thread
        self.__heartbeat_thread = None

    def settimeout(self, timeout: Optional[float]):
        self.__socket.settimeout(timeout)

    def connect(self, remote_host: str, remote_port: int):
        """ add remote address to keep connected with heartbeat """
        with self.__connections_lock:
            for conn in self.__connections:
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
                if conn.host == remote_host and conn.port == remote_port:
                    # got one
                    self.__connections.pop(pos)

    def __expired_connection(self) -> Optional[Connection]:
        """ get any expired connection """
        with self.__connections_lock:
            for conn in self.__connections:
                if conn.is_expired:
                    return conn

    def __refresh(self, remote_host: str, remote_port: int) -> bool:
        """ update connection's expired time """
        with self.__connections_lock:
            for conn in self.__connections:
                if conn.host == remote_host and conn.port == remote_port:
                    # refresh time
                    conn.update_expired_time()
                    return True

    def send(self, data: bytes, remote_host: str, remote_port: int) -> int:
        try:
            res = self.__socket.sendto(data, (remote_host, remote_port))
            if res == len(data):
                self.__refresh(remote_host=remote_host, remote_port=remote_port)
            return res
        except socket.error:
            return -1

    def __receive(self, buffer_size: int=2048) -> (bytes, tuple):
        try:
            data, address = self.__socket.recvfrom(buffer_size)
            if data is not None:
                assert len(address) == 2, 'remote address error: %s, data length: %d' % (address, len(data))
                self.__refresh(remote_host=address[0], remote_port=address[1])
            return data, address
        except socket.error:
            return None, None

    def run(self):
        while self.running:
            data, address = self.__receive()
            if data is None:
                time.sleep(0.1)
                continue
            assert len(address) == 2, 'address error' + address
            if len(data) == 4:
                # check heartbeat
                if data == b'PING':
                    self.send(data=b'PONG', remote_host=address[0], remote_port=address[1])
                    continue
                elif data == b'PONG':
                    # do nothing
                    continue
            self.delegate.received(data=data, source=address, destination=self.__local_address)

    def start(self):
        super().start()
        assert self.__heartbeat_thread is None, 'heartbeat thread already exists'
        t = threading.Thread(target=self.heartbeat, args=(self,))
        t.start()
        self.__heartbeat_thread = t

    def heartbeat(self):
        while self.running:
            time.sleep(2)
            while True:
                conn = self.__expired_connection()
                if conn is None:
                    # no expired connection now
                    break
                self.send(data=b'PING', remote_host=conn.host, remote_port=conn.port)
