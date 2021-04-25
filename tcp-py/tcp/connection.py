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


class Connection(threading.Thread):

    EXPIRES = 28  # seconds

    def __init__(self, address: tuple, sock: socket.socket = None):
        super().__init__()
        self.__sock = sock
        self.__address = address
        self.__host = address[0]
        self.__port = address[1]
        self.__started = False
        self.__running = False
        self.__status = ConnectionStatus.Default
        self.__delegate: Optional[weakref.ReferenceType] = None
        # initialize times to expired
        now = time.time()
        self.__last_sent_time = now - self.EXPIRES - 1
        self.__last_received_time = now - self.EXPIRES - 1
        # cache pool
        self.__pool = self._create_pool()

    def __del__(self):
        self.stop()

    # noinspection PyMethodMayBeStatic
    def _create_pool(self) -> Pool:
        return MemPool()

    @property
    def delegate(self):  # -> Optional[ConnectionHandler]:
        if self.__delegate is not None:
            return self.__delegate()

    @delegate.setter
    def delegate(self, value):
        if value is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(value)

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port

    @property
    def address(self) -> tuple:
        return self.__address

    @property
    def socket(self) -> socket.socket:
        return self.__sock

    @socket.setter
    def socket(self, value):
        self.__sock = value

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
                delegate.connection_status_changed(connection=self, old_status=old, new_status=value)

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
        if now < self.__last_received_time + self.EXPIRES:
            # received response recently
            if now < self.__last_sent_time + self.EXPIRES:
                # sent recently, set status = 'connected'
                self.__status = ConnectionStatus.Connected
            else:
                # long time no sending, set status = 'expired'
                self.__status = ConnectionStatus.Expired
            return self.__status
        if self.__status != ConnectionStatus.Default:
            # any status except 'initialized'
            if now > self.__last_received_time + (self.EXPIRES << 2):
                # long long time no response, set status = 'error'
                self.__status = ConnectionStatus.Error
                return self.__status
        # check with current status
        if self.__status == ConnectionStatus.Default:
            # case: 'default'
            if now < self.__last_sent_time + self.EXPIRES:
                # sent recently, change status to 'connecting'
                self.__status = ConnectionStatus.Connecting
        elif self.__status == ConnectionStatus.Connecting:
            # case: 'connecting'
            if now > self.__last_sent_time + self.EXPIRES:
                # long time no sending, change status to 'not_connect'
                self.__status = ConnectionStatus.Default
        elif self.__status == ConnectionStatus.Connected:
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
            if now < self.__last_sent_time + self.EXPIRES:
                # sent recently, change status to 'maintaining'
                self.__status = ConnectionStatus.Maintaining
        elif self.__status == ConnectionStatus.Maintaining:
            # case: 'maintaining'
            if now > self.__last_sent_time + self.EXPIRES:
                # long time no sending, change status to 'maintain_expired'
                self.__status = ConnectionStatus.Expired
        return self.__status

    def __update_sent_time(self, now: float):
        self.__last_sent_time = now

    def __update_received_time(self, now: float):
        self.__last_received_time = now

    def _read(self) -> Optional[bytes]:
        data = self.__sock.recv(1024)
        self.__update_received_time(now=time.time())
        return data

    def _write(self, data: bytes) -> int:
        self.__sock.sendall(data)
        self.__update_sent_time(now=time.time())
        return len(data)

    def send(self, data: bytes) -> int:
        """
        Send data package

        :param data: package
        :return: -1 on error
        """
        if self.__started:
            return self._write(data=data)

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

    def start(self):
        # check running
        tick = 0
        while self.__running:
            # waiting for last run loop exit
            time.sleep(0.1)
            tick += 1
            if tick > 100:
                # timeout (10 seconds)
                break
        # do start
        if not self.__started:
            super().start()

    def stop(self):
        self.__started = False

    def run(self):
        self.__started = True
        self.__running = True
        while self.__started:
            # 1. try to read bytes
            data = self._read()
            if data is None:
                # received nothing, have a rest ^_^
                time.sleep(0.1)
                continue
            data = self.__pool.cache(data=data)
            delegate = self.delegate
            if delegate is not None:
                # from .handler import ConnectionHandler
                # assert isinstance(delegate, ConnectionHandler), 'connection delegate error: %s' % delegate
                if data is None:
                    delegate.connection_received_data(connection=self)
                else:
                    delegate.connection_overflowed(connection=self, ejected=data)
        # stop running
        self.__running = False
