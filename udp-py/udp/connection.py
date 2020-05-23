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

    Error = -1
    Default = 0
    Connecting = 1
    Connected = 2


class Connection:

    EXPIRES = 28  # seconds

    def __init__(self, local_address: tuple, remote_address: tuple):
        super().__init__()
        self.__local_address = local_address
        self.__remote_address = remote_address
        # connecting time
        now = time.time()
        self.__connection_lost = now + (self.EXPIRES << 2)
        self.__receive_expired = now + self.EXPIRES
        self.__send_expired = now + self.EXPIRES

    @property
    def local_address(self) -> tuple:
        """ local ip, port """
        return self.__local_address

    @property
    def remote_address(self) -> tuple:
        """ remote ip, port """
        return self.__remote_address

    @property
    def status(self) -> ConnectionStatus:
        now = time.time()
        if now < self.__receive_expired:
            """
            When received a package from remote address, this node must respond
            a package, so 'send expired' is always late than 'receive expired'.
            So, if received anything (normal package or just 'PING') from this
            connection, this indicates 'Connected'.
            """
            return ConnectionStatus.Connected
        elif now > self.__connection_lost:
            """
            It's a long time to receive nothing (even a 'PONG'), this connection
            may be already lost, needs to reconnect again.
            """
            return ConnectionStatus.Error
        elif now < self.__send_expired:
            """
            If sent package through this connection recently but not received
            anything yet (includes 'PONG'), this indicates 'Connecting'.
            """
            return ConnectionStatus.Connecting
        else:
            """
            It's a long time to send nothing, this connection needs maintaining,
            send something immediately (e.g.: 'PING') to keep it alive.
            """
            return ConnectionStatus.Default

    def update_sent_time(self):
        """ update last send time """
        self.__send_expired = time.time() + self.EXPIRES

    def update_received_time(self):
        """ update last send time """
        now = time.time()
        self.__connection_lost = now + (self.EXPIRES << 2)
        self.__receive_expired = now + self.EXPIRES


class Cargo:

    def __init__(self, data: bytes, source: tuple):
        super().__init__()
        self.data = data
        self.source = source


class Socket(threading.Thread):
    
    """
        Max count for caching packages
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        Each UDP data package is limited to no more than 576 bytes, so set the
        MAX_CACHE_SPACES to about 2,000,000 means it would take up to 1GB memory
        for the caching.
    """
    MAX_CACHE_SPACES = 1024 * 1024 * 2

    def __init__(self, port: int, host: str='0.0.0.0'):
        super().__init__()
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

    @property
    def running(self) -> bool:
        return not getattr(self.__socket, '_closed', False)

    @staticmethod
    def _create_socket() -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock

    def settimeout(self, timeout: Optional[float]):
        self.__socket.settimeout(timeout)

    def get_connection(self, remote_address: tuple) -> Optional[Connection]:
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    # got it
                    return conn

    def connect(self, remote_address: tuple):
        """ add remote address to keep connected with heartbeat """
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    # already connected
                    return
            conn = Connection(local_address=self.local_address, remote_address=remote_address)
            self.__connections.append(conn)

    def disconnect(self, remote_address: tuple):
        """ remove remote address from heartbeat tasks """
        with self.__connections_lock:
            pos = len(self.__connections)
            while pos > 0:
                pos -= 1
                conn = self.__connections[pos]
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    # got one
                    self.__connections.pop(pos)
                    # break

    def __expired_connection(self) -> Optional[Connection]:
        """ get any expired connection """
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.status == ConnectionStatus.Default:
                    return conn

    def __error_connection(self) -> Optional[Connection]:
        """ get any error connection """
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.status == ConnectionStatus.Error:
                    return conn

    def __update_sent_time(self, remote_address: tuple):
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    # refresh time
                    conn.update_sent_time()
                    # return True

    def __update_received_time(self, remote_address: tuple):
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    # refresh time
                    conn.update_received_time()
                    # return True

    def send(self, data: bytes, remote_address: tuple) -> int:
        """
        Send data to remote address

        :param data:
        :param remote_address:
        :return: how many bytes have been sent
        """
        try:
            res = self.__socket.sendto(data, remote_address)
            assert res == len(data), 'send failed: %d, %d' % (res, len(data))
            self.__update_sent_time(remote_address=remote_address)
            return res
        except socket.error as error:
            print('Failed to send data: %s' % error)
            return -1

    def __receive(self, buffer_size: int=2048) -> (bytes, (str, int)):
        try:
            data, address = self.__socket.recvfrom(buffer_size)
            if data is not None:
                assert len(address) == 2, 'remote address error: %s, data length: %d' % (address, len(data))
                self.__update_received_time(remote_address=address)
            return data, address
        except socket.error as error:
            if not isinstance(error, socket.timeout):
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

    def __cache(self, data: bytes, source: tuple):
        with self.__cargoes_lock:
            if len(self.__cargoes) >= self.MAX_CACHE_SPACES:
                # drop the first package
                self.__cargoes.pop(0)
            # append the new package to the end
            self.__cargoes.append(Cargo(data=data, source=source))

    def run(self):
        self.settimeout(2)
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
                        self.send(data=b'PONG', remote_address=address)
                        continue
                    elif data == b'PONG':
                        # ignore it
                        continue
                # cache the data received
                self.__cache(data=data, source=address)
            except Exception as error:
                print('socket error: %s' % error)

    def ping(self):
        """ send heartbeat to all expired connections """
        while True:
            conn = self.__expired_connection()
            if conn is None:
                # no more expired connection
                break
            self.send(data=b'PING', remote_address=conn.remote_address)

    def purge(self):
        """ remove error connections """
        while True:
            conn = self.__error_connection()
            if conn is None:
                # no more error connection
                break
            # remove error connection (long time to receive nothing)
            self.disconnect(remote_address=conn.remote_address)

    def close(self):
        self.__socket.close()

    def stop(self):
        self.close()
