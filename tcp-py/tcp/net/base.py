# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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

from ..fsm import Delegate as StateDelegate

from .channel import Channel
from .connection import Connection, Delegate as ConnectionDelegate
from .state import ConnectionState, StateMachine


class BaseConnection(Connection, StateDelegate):

    EXPIRES = 16  # seconds

    def __init__(self, channel: Optional[Channel]):
        super().__init__()
        self._channel = channel
        self.__last_sent_time = 0
        self.__last_received_time = 0
        self.__delegate: Optional[weakref.ReferenceType] = None
        # Finite State Machine
        self.__fsm = StateMachine(connection=self)
        self.__fsm.delegate = self

    @property
    def delegate(self) -> ConnectionDelegate:
        if self.__delegate is not None:
            return self.__delegate()

    @delegate.setter
    def delegate(self, handler: ConnectionDelegate):
        if handler is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(handler)

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        elif isinstance(other, Connection):
            return self.remote_address == other.remote_address and self.local_address == other.local_address

    def __ne__(self, other) -> bool:
        if self is other:
            return False
        elif isinstance(other, Connection):
            return self.remote_address != other.remote_address or self.local_address != other.local_address
        else:
            return True

    def __hash__(self) -> int:
        local = self.local_address
        remote = self.remote_address
        if remote is None:
            assert local is not None, 'both local & remote addresses are empty'
            return hash(local)
        # same algorithm as Pair::hashCode()
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # remote's hashCode is multiplied by an arbitrary prime number (13)
        # in order to make sure there is a difference in the hashCode between
        # these two parameters:
        #     remote: a  local: aa
        #     local: aa  remote: a
        if local is None:
            return hash(remote) * 13
        else:
            return hash(remote) * 13 + hash(local)

    @property
    def sent_recently(self) -> bool:
        now = time.time()
        return now < self.__last_sent_time + self.EXPIRES

    @property
    def received_recently(self) -> bool:
        now = time.time()
        return now < self.__last_received_time + self.EXPIRES

    @property
    def long_time_not_received(self) -> bool:
        now = time.time()
        return now > self.__last_received_time + (self.EXPIRES << 4)

    @property
    def channel(self) -> Channel:
        sock = self._channel
        if sock is None or not sock.opened:
            raise ConnectionError('connection lost: %s' % sock)
        return sock

    #
    #   Connection
    #

    @property
    def opened(self) -> bool:
        sock = self.channel
        return sock is not None and sock.opened

    @property
    def bound(self) -> bool:
        sock = self.channel
        return sock is not None and sock.bound

    @property
    def connected(self) -> bool:
        sock = self.channel
        return sock is not None and sock.connected

    @property
    def local_address(self) -> Optional[tuple]:  # (str, int)
        sock = self._channel
        if sock is not None:
            return sock.local_address

    @property
    def remote_address(self) -> Optional[tuple]:  # (str, int)
        sock = self._channel
        if sock is not None:
            return sock.remote_address

    def send(self, data: bytes, target: Optional[tuple] = None) -> int:
        try:
            sent = self.channel.send(data=data, target=target)
            if sent != -1:
                self.__last_sent_time = time.time()
            return sent
        except socket.error as error:
            print('[NET] failed to send data: %s' % error)
            self.close()
            self.change_state(name=ConnectionState.ERROR)
            return -1

    def receive(self, max_len: int) -> (bytes, tuple):
        try:
            data, remote = self.channel.receive(max_len=max_len)
            if data is not None and len(data) > 0:
                self.__last_received_time = time.time()
            return data, remote
        except socket.error as error:
            print('[NET] failed to receive data: %s' % error)
            self.close()
            self.change_state(name=ConnectionState.ERROR)
            return None, None

    def close(self):
        sock = self._channel
        try:
            if sock is not None and sock.opened:
                sock.close()
        except socket.error as error:
            print('[NET] failed to close socket: %s' % error)
        finally:
            self._channel = None
            self.change_state(name=ConnectionState.DEFAULT)

    #
    #   States
    #

    def change_state(self, name: str):
        state = self.__fsm.get_state(name=name)
        if state != self.__fsm.current_state:
            self.__fsm.change_state(state=state)

    @property
    def state(self) -> ConnectionState:
        current = self.__fsm.current_state
        if isinstance(current, ConnectionState):
            return current

    #
    #   Ticker
    #
    def tick(self):
        self.__fsm.tick()

    def start(self):
        self.__fsm.start()

    def stop(self):
        self.__fsm.stop()

    #
    #   StateDelegate
    #
    def enter_state(self, state: ConnectionState, ctx: StateMachine):
        current = ctx.current_state
        if state == ConnectionState.CONNECTED:
            if current != ConnectionState.MAINTAINING:
                # change state to 'connected', reset times to just expired
                timestamp = time.time() - self.EXPIRES - 1
                self.__last_sent_time = timestamp
                self.__last_received_time = timestamp
        # callback
        delegate = self.delegate
        if delegate is not None:
            delegate.connection_state_changing(connection=self, current_state=current, next_state=state)

    def exit_state(self, state: ConnectionState, ctx: StateMachine):
        pass

    def pause_state(self, state: ConnectionState, ctx: StateMachine):
        pass

    def resume_state(self, state: ConnectionState, ctx: StateMachine):
        pass