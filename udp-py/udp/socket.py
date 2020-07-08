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

import socket
import threading
import time
import weakref
from typing import Optional

from .connection import ConnectionHandler, Connection, DatagramPacket


class Socket(threading.Thread):

    """
        Max count for caching packages
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Each UDP data package is limited to no more than 576 bytes, so set the
        MAX_CACHE_SPACES to about 2,000,000 means it would take up to 1GB memory
        for caching on one socket.
    """
    MAX_CACHE_SPACES = 1024 * 1024 * 2

    """
        Maximum Transmission Unit
        ~~~~~~~~~~~~~~~~~~~~~~~~~
        
        Buffer size for receiving package
    """
    MTU = 1472  # 1500 - 20 - 8

    def __init__(self, port: int, host: str ='0.0.0.0'):
        super().__init__()
        self.__local_address = (host, port)
        self.__host = host
        self.__port = port
        # create socket
        self.__socket = self._create_socket()
        # connection handler
        self.__handler: weakref.ReferenceType = None
        # connection list
        self.__connections = set()
        self.__connections_lock = threading.Lock()
        # declaration forms
        self.__declarations = []
        self.__declarations_lock = threading.Lock()

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port

    def _create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(2)
        sock.bind(self.local_address)
        return sock

    def settimeout(self, timeout: Optional[float]):
        self.__socket.settimeout(timeout)

    @property
    def handler(self) -> Optional[ConnectionHandler]:
        if self.__handler is not None:
            return self.__handler()

    @handler.setter
    def handler(self, value: ConnectionHandler):
        if value is None:
            self.__handler = None
        else:
            self.__handler = weakref.ref(value)

    #
    #  Connections
    #

    def get_connection(self, remote_address: tuple) -> Optional[Connection]:
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    return conn

    # noinspection PyMethodMayBeStatic
    def _create_connection(self, remote_address: tuple, local_address: tuple=None) -> Connection:
        return Connection(local_address=local_address, remote_address=remote_address)

    def connect(self, remote_address: tuple) -> Connection:
        """ add remote address to keep connected with heartbeat """
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    # already connected
                    return conn
            conn = self._create_connection(remote_address=remote_address, local_address=self.local_address)
            self.__connections.add(conn)
            return conn

    def disconnect(self, remote_address: tuple) -> set:
        """ remove remote address from heartbeat tasks """
        removed_connections = set()
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.remote_address == remote_address:
                    # got one
                    removed_connections.add(conn)
                    # break
            for conn in removed_connections:
                self.__connections.remove(conn)
        # clear declaration forms
        self.__clear_declarations(connections=removed_connections)
        return removed_connections

    def __clear_declarations(self, connections: set):
        with self.__declarations_lock:
            for conn in connections:
                self.__remove_declarations(remote_address=conn.remote_address)

    def __remove_declarations(self, remote_address: tuple):
        index = len(self.__declarations) - 1
        while index >= 0:
            if remote_address == self.__declarations[index]:
                self.__declarations.pop(index)
            index += 1

    def __expired_connection(self) -> Optional[Connection]:
        """ get any expired connection """
        now = time.time()
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.is_expired(now=now):
                    return conn

    def __error_connection(self) -> Optional[Connection]:
        """ get any error connection """
        now = time.time()
        with self.__connections_lock:
            for conn in self.__connections:
                assert isinstance(conn, Connection), 'connection error: %s' % conn
                if conn.is_error(now=now):
                    return conn

    def __update_sent_time(self, remote_address: tuple):
        conn = self.get_connection(remote_address=remote_address)
        if conn is None:
            return
        now = time.time()
        # 1. get old status
        old_status = conn.get_status(now=now)
        # 2. refresh time
        conn.update_sent_time(now=now)
        # 3. get new status
        new_status = conn.get_status(now=now)
        if old_status == new_status:
            return
        # callback
        handler = self.handler
        if handler is not None:
            handler.connection_status_changed(connection=conn, old_status=old_status, new_status=new_status)

    def __update_received_time(self, remote_address: tuple):
        conn = self.get_connection(remote_address=remote_address)
        if conn is None:
            return
        now = time.time()
        # 1. get old status
        old_status = conn.get_status(now=now)
        # 2. refresh time
        conn.update_received_time(now=now)
        # 3. get new status
        new_status = conn.get_status(now=now)
        if old_status == new_status:
            return
        # callback
        handler = self.handler
        if handler is not None:
            handler.connection_status_changed(connection=conn, old_status=old_status, new_status=new_status)

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

    def __receive(self, buffer_size: int = 2048) -> Optional[DatagramPacket]:
        try:
            data, address = self.__socket.recvfrom(buffer_size)
            if data is not None:
                assert len(address) == 2, 'remote address error: %s, data length: %d' % (address, len(data))
                self.__update_received_time(remote_address=address)
                return DatagramPacket(data=data, address=address)
        except socket.error as error:
            if not isinstance(error, socket.timeout):
                print('Failed to receive data: %s' % error)

    def receive(self) -> Optional[DatagramPacket]:
        """
        Get received data package from buffer, non-blocked

        :return: received data and source address
        """
        with self.__declarations_lock:
            while len(self.__declarations) > 0:
                # get first one
                address = self.__declarations.pop(0)
                conn = self.get_connection(remote_address=address)
                if conn is None:
                    # connection lost, remove all declaration forms with its socket address
                    self.__remove_declarations(remote_address=address)
                cargo = conn.receive()
                if cargo is not None:
                    # got one packet
                    return cargo

    def __cache(self, packet: DatagramPacket):
        # 1. get connection by address in packet
        address = packet.address
        conn = self.get_connection(remote_address=address)
        if conn is None:
            # NOTICE:
            #     If received a package, not heartbeat (PING, PONG)
            #     create a connection for caching it.
            conn = self.connect(remote_address=address)
        with self.__declarations_lock:
            # 2. append packet to connection's cache
            ejected = conn.cache(packet=packet)
            # NOTICE:
            #     If something ejected, means this connection's cache is full,
            #     don't append new form for it, just keep the old ones in queue,
            #     this will let the old forms have a higher priority
            #     to be processed as soon as possible.
            if ejected is None:
                # append the new form to the end
                self.__declarations.append(address)
            # 3. check socket memory status
            if self._is_cache_full(count=len(self.__declarations), remote_address=address):
                # NOTICE:
                #     this socket is full, eject one cargo from any connection.
                #     notice that the connection which cache is full will have
                #     a higher priority to be ejected.
                self.receive()
        # 4. callback
        delegate = self.handler
        if delegate is not None:
            delegate.connection_received_data(connection=conn)

    # noinspection PyUnusedLocal
    def _is_cache_full(self, count: int, remote_address: tuple) -> bool:
        return count > self.MAX_CACHE_SPACES

    # def start(self):
    #     if self.isAlive():
    #         return
    #     super().start()

    def stop(self):
        self.close()

    def close(self):
        # TODO: disconnect all connections (clear declaration forms)
        self.__socket.close()

    @property
    def running(self) -> bool:
        return not getattr(self.__socket, '_closed', False)

    def run(self):
        while self.running:
            try:
                packet = self.__receive(buffer_size=self.MTU)
                if packet is None:
                    # receive nothing
                    time.sleep(0.1)
                    continue
                if packet.length == 4:
                    # check heartbeat
                    data = packet.data
                    if data == b'PING':
                        # respond heartbeat
                        self.send(data=b'PONG', remote_address=packet.address)
                        continue
                    elif data == b'PONG':
                        # ignore it
                        continue
                # cache the data received
                self.__cache(packet=packet)
            except Exception as error:
                print('Socket.run error: %s' % error)

    def ping(self) -> int:
        """ send heartbeat to all expired connections """
        count = 0
        while True:
            conn = self.__expired_connection()
            if conn is None:
                # no more expired connection
                break
            self.send(data=b'PING', remote_address=conn.remote_address)
            count += 1
        return count

    def purge(self) -> set:
        """ remove error connections """
        all_connections = set()
        while True:
            conn = self.__error_connection()
            if conn is None:
                # no more error connection
                break
            # remove error connection (long time to receive nothing)
            removed_connections = self.disconnect(remote_address=conn.remote_address)
            if len(removed_connections) > 0:
                all_connections = all_connections.union(removed_connections)
        return all_connections
