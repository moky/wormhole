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
import time
import weakref
from typing import Optional

from .pool import Pool
from .mem import LockedPool
from .status import ConnectionStatus
from .delegate import ConnectionDelegate
from .connection import Connection


class BaseConnection(Connection):

    def __init__(self, sock: Optional[socket.socket] = None):
        super().__init__()
        self.__pool = self._create_pool()
        self.__delegate: Optional[weakref.ReferenceType] = None
        self._sock = sock
        self._running = False
        self.__status = ConnectionStatus.Default
        self.__last_sent_time = 0
        self.__last_received_time = 0
        # FSM
        self.__fsm_evaluations = {}
        self.__fsm_init()

    # noinspection PyMethodMayBeStatic
    def _create_pool(self) -> Pool:
        return LockedPool()

    @property
    def delegate(self) -> Optional[ConnectionDelegate]:
        if self.__delegate is not None:
            return self.__delegate()

    @delegate.setter
    def delegate(self, handler: ConnectionDelegate):
        if handler is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(handler)

    #
    #   Socket
    #

    @property
    def socket(self) -> Optional[socket.socket]:
        """ Get connected socket """
        if self.alive:
            return self._sock

    @property
    def address(self) -> Optional[tuple]:
        sock = self._sock
        if sock is not None:
            return sock.getpeername()

    @property
    def alive(self) -> bool:
        if self._running:
            sock = self._sock
            if sock is None or getattr(sock, '_closed', False):
                return False
            else:
                return True

    def __write(self, data: bytes) -> int:
        # sock.sendall(data)
        sock = self._sock
        assert sock is not None, 'cannot write data when socket is closed: %s' % sock
        sent = 0
        rest = len(data)
        while rest > 0:  # and not getattr(sock, '_closed', False):
            cnt = sock.send(data)
            if cnt > 0:
                sent += cnt
                rest -= cnt
                data = data[cnt:]
        # done
        self.__last_sent_time = time.time()
        return sent

    def __read(self) -> Optional[bytes]:
        sock = self._sock
        assert sock is not None, 'cannot read data when socket is closed: %s' % sock
        data = sock.recv(512)
        if data is None or len(data) == 0:
            if sock.gettimeout() is None:
                raise socket.error('remote peer reset socket')
        self.__last_received_time = time.time()
        return data

    def __close(self):
        sock = self._sock
        if isinstance(sock, socket.socket) and not getattr(sock, '_closed', False):
            # sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        self._sock = None

    def _receive(self) -> Optional[bytes]:
        sock = self.socket
        if sock is not None:
            try:
                return self.__read()
            except socket.error as error:
                print('[TCP] failed to receive data: %s' % error)
                self.__close()
        self.status = ConnectionStatus.Error

    # Override
    def send(self, data: bytes) -> int:
        sock = self.socket
        if sock is not None:
            try:
                return self.__write(data=data)
            except socket.error as error:
                print('[TCP] failed to send data: %d, %s' % (len(data), error))
                self.__close()
        self.status = ConnectionStatus.Error
        return -1

    @property
    def available(self) -> int:
        return self.__pool.length

    # Override
    def received(self) -> Optional[bytes]:
        return self.__pool.all()

    # Override
    def receive(self, max_length: int) -> Optional[bytes]:
        return self.__pool.pop(max_length=max_length)

    #
    #   Status
    #

    @property
    def status(self) -> ConnectionStatus:
        self.__fsm_tick(now=time.time())
        return self.__status

    @status.setter
    def status(self, value: ConnectionStatus):
        old = self.__status
        if old != value:
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

    #
    #   Runnable
    #

    # Override
    def run(self):
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    # Override
    def stop(self):
        self._running = False

    def setup(self):
        """ Prepare before handling """
        self._running = True
        self.status = ConnectionStatus.Connecting

    def finish(self):
        """ Cleanup after handling """
        self._running = False
        if self._sock is not None:
            # shutdown socket
            self.__close()
        self.status = ConnectionStatus.Default

    def handle(self):
        """ Handling for receiving data packages
            (it will call 'process()' circularly)
        """
        while self.alive:
            s = self.status
            if s in [ConnectionStatus.Connected, ConnectionStatus.Maintaining, ConnectionStatus.Expired]:
                working = self.process()
            else:
                working = False
            if not working:
                self._idle()

    def process(self) -> bool:
        """ Try to receive one data package,
            which will be cached into a memory pool
        """
        # 0. check empty spaces
        count = self.__pool.length
        if count >= self.MAX_CACHE_LENGTH:
            # not enough spaces
            return False
        # 1. try to read bytes
        data = self._receive()
        if data is None or len(data) == 0:
            return False
        # 2. cache it
        self.__pool.push(data=data)
        delegate = self.delegate
        if delegate is not None:
            # 3. callback
            delegate.connection_received(connection=self, data=data)
        return True

    # noinspection PyMethodMayBeStatic
    def _idle(self):
        time.sleep(0.1)

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

    def __fsm_tick(self, now: float):
        tick = self.__fsm_evaluations.get(self.__status)
        if tick is not None:
            tick(now=now)

    # noinspection PyUnusedLocal
    def __tick_default(self, now: float):
        """ Connection not started yet """
        if self._running:
            # connection started, change status to 'connecting'
            self.status = ConnectionStatus.Connecting

    # noinspection PyUnusedLocal
    def __tick_connecting(self, now: float):
        """ Connection started, not connected yet """
        if not self._running:
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
        if not self._running:
            # connection stopped, change status to 'not_connect'
            self.status = ConnectionStatus.Default
        elif self.socket is not None:
            # connection reconnected, change status to 'connected'
            self.status = ConnectionStatus.Connected
