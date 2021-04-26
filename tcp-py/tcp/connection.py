# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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

from .pool import Pool
from .mem import MemPool
from .status import ConnectionStatus
from .delegate import ConnectionDelegate


class Connection(threading.Thread):

    EXPIRES = 16  # seconds

    def __init__(self, address: Optional[tuple] = None, sock: Optional[socket.socket] = None):
        super().__init__()
        # 'address' and 'sock' should not be None both at same time
        self.__address = address
        self.__socket = sock
        # connection status
        if sock is None:
            self.__status = ConnectionStatus.Default
        elif getattr(sock, '_closed', False):
            self.__status = ConnectionStatus.Error
        else:
            self.__status = ConnectionStatus.Connected
        # connect delegate
        self.__delegate: Optional[weakref.ReferenceType] = None
        self.__running = False
        # initialize times to expired
        now = time.time()
        self.__last_sent_time = now - self.EXPIRES - 1
        self.__last_received_time = now - self.EXPIRES - 1
        # cache pool
        self.__pool = self._create_pool()

    @property
    def address(self) -> Optional[tuple]:
        """ (IP, Port) """
        if self.__address is None:
            if self.__socket is not None:
                return self.__socket.getpeername()
        else:
            return self.__address

    @property
    def socket(self) -> socket.socket:
        if self.__socket is None:
            if self.__address is None:
                # server connection lost
                self.status = ConnectionStatus.Error
            else:
                # client connection
                self.status = ConnectionStatus.Connecting
                try:
                    sock = socket.socket()
                    sock.connect(self.__address)
                    self.__socket = sock
                    self.status = ConnectionStatus.Connected
                except socket.error as error:
                    print('[TCP] failed to connect: %s, %s' % (self.__address, error))
                    self.status = ConnectionStatus.Error
        return self.__socket

    def __write(self, data: bytes) -> int:
        sock = self.socket
        if sock is not None:
            sock.sendall(data)
            self.__last_sent_time = time.time()
            return len(data)
        else:
            return -1

    def __read(self) -> Optional[bytes]:
        sock = self.socket
        if sock is not None:
            data = sock.recv(512)
            self.__last_received_time = time.time()
            return data

    #
    #   Connection Status
    #

    @property
    def status(self) -> ConnectionStatus:
        return self.__status

    @status.setter
    def status(self, value: ConnectionStatus):
        if self.__status != value:
            old = self.__status
            self.__status = value
            # callback
            delegate = self.delegate
            if delegate is not None:
                # from .handler import ConnectionHandler
                # assert isinstance(delegate, ConnectionHandler), 'connection delegate error: %s' % delegate
                delegate.connection_changed(connection=self, old_status=old, new_status=value)

    def is_connected(self, now: float) -> bool:
        status = self.get_status(now=now)
        return ConnectionStatus.is_connected(status=status)

    def is_expired(self, now: float) -> bool:
        status = self.get_status(now=now)
        return ConnectionStatus.is_expired(status=status)

    def is_error(self, now: float) -> bool:
        status = self.get_status(now=now)
        return ConnectionStatus.is_error(status=status)

    def get_status(self, now: float):
        """
        Get connection status

        :param now: timestamp in seconds
        :return: new status
        """
        # pre-checks
        if self.__status == ConnectionStatus.Default:
            # case: 'default'
            if now < self.__last_sent_time + self.EXPIRES:
                # sent recently, change status to 'connecting'
                self.__status = ConnectionStatus.Connecting
                return self.__status
        else:
            if self.__status == ConnectionStatus.Connecting:
                # case: 'connecting'
                if now > self.__last_sent_time + self.EXPIRES:
                    # long time no sending, change status to 'not_connect'
                    self.__status = ConnectionStatus.Default
                    return self.__status
            # any status except 'initialized'
            if now > self.__last_received_time + (self.EXPIRES << 2):
                # long long time no response, set status = 'error'
                self.__status = ConnectionStatus.Error
                return self.__status
        # check with current status
        if self.__status == ConnectionStatus.Connected:
            # case: 'connected'
            if now > self.__last_received_time + self.EXPIRES:
                # long time no response, needs maintaining
                if now < self.__last_sent_time + self.EXPIRES:
                    # sent recently, change status to 'maintaining'
                    self.__status = ConnectionStatus.Maintaining
                else:
                    # long time no sending, change status to 'maintain_expired'
                    self.__status = ConnectionStatus.Expired
        elif self.__status == ConnectionStatus.Expired:
            # case: 'maintain_expired'
            if now < self.__last_received_time + self.EXPIRES:
                # received recently, change status to 'connected'
                self.__status = ConnectionStatus.Connected
            elif now < self.__last_sent_time + self.EXPIRES:
                # sent recently, change status to 'maintaining'
                self.__status = ConnectionStatus.Maintaining
        elif self.__status == ConnectionStatus.Maintaining:
            # case: 'maintaining'
            if now < self.__last_received_time + self.EXPIRES:
                # received recently, change status to 'connected'
                self.__status = ConnectionStatus.Connected
            if now > self.__last_sent_time + self.EXPIRES:
                # long time no sending, change status to 'maintain_expired'
                self.__status = ConnectionStatus.Expired
        # return new status
        return self.__status

    #
    #   Connection Delegate
    #

    @property
    def delegate(self) -> Optional[ConnectionDelegate]:
        if self.__delegate is not None:
            return self.__delegate()

    @delegate.setter
    def delegate(self, value: ConnectionDelegate):
        if value is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(value)

    # noinspection PyMethodMayBeStatic
    def _create_pool(self) -> Pool:
        return MemPool()

    def received(self) -> Optional[bytes]:
        """
        Get received data from cache, but not remove

        :return: received data
        """
        return self.__pool.received()

    def receive(self, length: int) -> Optional[bytes]:
        """
        Get received data from cache, and remove it
        (call received to check data first)

        :param length: how many bytes to receive
        :return: received data
        """
        return self.__pool.receive(length=length)

    def send(self, data: bytes) -> int:
        """
        Send data package

        :param data: package
        :return: -1 on error
        """
        try:
            return self.__write(data=data)
        except socket.error as error:
            print('[TCP] failed to send data: %d, %s' % (len(data), error))
            self.__socket = None
        if self.__address is not None:
            # reconnect and try again
            time.sleep(0.1)
            try:
                return self.__write(data=data)
            except socket.error as error:
                print('[TCP] failed to send data again: %d, %s' % (len(data), error))
                self.__socket = None
        # failed
        return -1

    def __receive(self) -> Optional[bytes]:
        try:
            return self.__read()
        except socket.error as error:
            print('[TCP] failed to receive data: %s' % error)
            self.__socket = None
        if self.__address is not None:
            # reconnect and try again
            time.sleep(0.1)
            try:
                return self.__read()
            except socket.error as error:
                print('[TCP] failed to receive data again: %s' % error)
                self.__socket = None
        # failed
        return None

    def handle(self):
        # 1. try to read bytes
        data = self.__receive()
        if data is not None:
            ejected = self.__pool.cache(data=data)
            delegate = self.delegate
            if delegate is not None:
                delegate.connection_received(connection=self, data=data)
                if ejected is not None:
                    delegate.connection_overflowed(connection=self, ejected=ejected)

    def run(self):
        self.__running = True
        while self.__running:
            try:
                self.handle()
            except Exception as error:
                print('[TCP] failed to handle connection: %s' % error)

    def stop(self):
        self.__running = False
        if self.__socket is not None:
            self.__socket.close()
            self.__socket = None
