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
        self.__status = ConnectionStatus.Default
        self.__delegate: Optional[weakref.ReferenceType] = None
        self.__running = False
        self.__last_sent_time = 0
        self.__last_received_time = 0
        # cache pool
        self.__pool = self._create_pool()
        # FSM
        self.__fsm_evaluations = {}
        self.__fsm_init()

    @property
    def address(self) -> Optional[tuple]:
        """ (IP, Port) """
        return self.__address

    @property
    def socket(self) -> Optional[socket.socket]:
        if self.__socket is None:
            if self.__address is None:
                return None
            if self.__status != ConnectionStatus.Connecting:
                return None
            try:
                sock = socket.socket()
                sock.connect(self.__address)
                self.__socket = sock
            except socket.error as error:
                print('[TCP] failed to connect: %s, %s' % (self.__address, error))
                self.status = ConnectionStatus.Error
                return None
        # check closed
        sock = self.__socket
        if sock is not None and not getattr(self.__socket, '_closed', False):
            return sock

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
            if value == ConnectionStatus.Connected and old != ConnectionStatus.Maintaining:
                # change status to 'connected', reset times to expired
                now = time.time()
                self.__last_sent_time = now - self.EXPIRES - 1
                self.__last_received_time = now - self.EXPIRES - 1
            # callback
            delegate = self.delegate
            if delegate is not None:
                delegate.connection_changed(connection=self, old_status=old, new_status=value)

    def get_status(self, now: float) -> ConnectionStatus:
        self.__tick(now=now)
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
            self.status = ConnectionStatus.Error
            return -1

    def __receive(self) -> Optional[bytes]:
        try:
            return self.__read()
        except socket.error as error:
            print('[TCP] failed to receive data: %s' % error)
            self.__socket = None
            self.status = ConnectionStatus.Error

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
                self.__tick(now=time.time())
                self.handle()
            except Exception as error:
                print('[TCP] failed to handle connection: %s' % error)

    def stop(self):
        self.__running = False
        # shutdown socket
        sock = self.__socket
        if isinstance(sock, socket.socket):
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        self.__socket = None
        self.status = ConnectionStatus.Default

    #
    #   Finite State Machine
    #

    def __fsm_init(self):
        self.__fsm_evaluations[ConnectionStatus.Default] = self.__tick_default
        self.__fsm_evaluations[ConnectionStatus.Connecting] = self.__tick_connecting
        self.__fsm_evaluations[ConnectionStatus.Connected] = self.__tick_connected
        self.__fsm_evaluations[ConnectionStatus.Maintaining] = self.__tick_maintaining
        self.__fsm_evaluations[ConnectionStatus.Expired] = self.__tick_expired
        self.__fsm_evaluations[ConnectionStatus.Error] = self.__tick_error

    # noinspection PyUnusedLocal
    def __tick_default(self, now: float):
        """ Connection not started yet """
        if self.__running:
            # connection started, change status to 'connecting'
            self.status = ConnectionStatus.Connecting

    # noinspection PyUnusedLocal
    def __tick_connecting(self, now: float):
        """ Connection started, not connected yet """
        if not self.__running:
            # connection stopped, change status to 'not_connect'
            self.status = ConnectionStatus.Default
        elif self.socket is not None:
            # connection connected, change status to 'connected'
            self.status = ConnectionStatus.Connected

    def __tick_connected(self, now: float):
        """ Normal status of connection """
        if self.socket is None:
            # connection lost, change status to 'error'
            self.status = ConnectionStatus.Error
        elif now > self.__last_received_time + self.EXPIRES:
            # long time no response, change status to 'maintain_expired'
            self.status = ConnectionStatus.Expired

    def __tick_expired(self, now: float):
        """ Long time no response, need maintaining """
        if self.socket is None:
            # connection lost, change status to 'error'
            self.status = ConnectionStatus.Error
        elif now < self.__last_sent_time + self.EXPIRES:
            # sent recently, change status to 'maintaining'
            self.status = ConnectionStatus.Maintaining

    def __tick_maintaining(self, now: float):
        """ Heartbeat sent, waiting response """
        if self.socket is None:
            # connection lost, change status to 'error'
            self.status = ConnectionStatus.Error
        elif now > self.__last_received_time + (self.EXPIRES << 4):
            # long long time no response, change status to 'error'
            self.status = ConnectionStatus.Error
        elif now < self.__last_received_time + self.EXPIRES:
            # received recently, change status to 'connected'
            self.status = ConnectionStatus.Connected
        elif now > self.__last_sent_time + self.EXPIRES:
            # long time no sending, change status to 'maintain_expired'
            self.status = ConnectionStatus.Expired

    # noinspection PyUnusedLocal
    def __tick_error(self, now: float):
        """ Connection lost """
        if not self.__running:
            # connection stopped, change status to 'not_connect'
            self.status = ConnectionStatus.Default
        elif self.socket is not None:
            # connection reconnected, change status to 'connected'
            self.status = ConnectionStatus.Connected

    def __tick(self, now: float):
        tick = self.__fsm_evaluations.get(self.__status)
        if tick is not None:
            tick(now=now)
