# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
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

from ..fsm import StateDelegate
from ..types import AddressPairObject

from .hub import Hub
from .channel import Channel
from .connection import Connection
from .delegate import ConnectionDelegate
from .state import ConnectionState, StateMachine, TimedConnection


class BaseConnection(AddressPairObject, Connection, TimedConnection, StateDelegate):

    EXPIRES = 16  # seconds

    def __init__(self, remote: tuple, local: Optional[tuple], channel: Channel, delegate: ConnectionDelegate, hub: Hub):
        super().__init__(remote=remote, local=local)
        self.__channel = channel
        # active times
        self.__last_sent_time = 0
        self.__last_received_time = 0
        # handlers
        self.__delegate = weakref.ref(delegate)
        self.__hub = weakref.ref(hub)
        # Finite State Machine
        self.__fsm = self._create_state_machine()

    # protected
    def _create_state_machine(self) -> StateMachine:
        fsm = StateMachine(connection=self)
        fsm.delegate = self
        return fsm

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    @property
    def hub(self) -> Hub:
        return self.__hub()

    @property  # protected
    def channel(self) -> Optional[Channel]:
        return self.__channel

    def _set_channel(self, channel: Channel):
        self.__channel = channel

    @property  # Override
    def opened(self) -> bool:
        sock = self.channel
        return sock is not None and sock.opened

    @property  # Override
    def bound(self) -> bool:
        sock = self.channel
        return sock is not None and sock.bound

    @property  # Override
    def connected(self) -> bool:
        sock = self.channel
        return sock is not None and sock.connected

    @property  # Override
    def alive(self) -> bool:
        return self.opened and (self.connected or self.bound)

    # Override
    def close(self):
        self.__close_channel()
        self.__fsm.stop()

    def __close_channel(self):
        sock = self.__channel
        if sock is not None:
            self.__channel = None
            hub = self.hub
            if hub is not None:
                hub.close_channel(channel=sock)

    @property  # Override
    def last_sent_time(self) -> int:
        return self.__last_sent_time

    @property  # Override
    def last_received_time(self) -> int:
        return self.__last_received_time

    # Override
    def is_sent_recently(self, now: int) -> bool:
        return now < self.__last_sent_time + self.EXPIRES

    # Override
    def is_received_recently(self, now: int) -> bool:
        return now < self.__last_received_time + self.EXPIRES

    # Override
    def is_long_time_not_received(self, now: int) -> bool:
        return now > self.__last_received_time + (self.EXPIRES << 3)

    # Override
    def received(self, data: bytes, remote: Optional[tuple], local: Optional[tuple]):
        self.__last_received_time = int(time.time())
        delegate = self.delegate
        if delegate is not None:
            delegate.connection_received(data=data, source=remote, destination=local, connection=self)

    # protected
    def _send(self, data: bytes, target: Optional[tuple]) -> int:
        sock = self.channel
        if sock is None or not sock.alive:
            raise socket.error('socket channel lost: %s' % sock)
        sent = sock.send(data=data, target=target)
        if sent != -1:
            self.__last_sent_time = int(time.time())
        return sent

    # Override
    def send(self, data: bytes, target: Optional[tuple] = None) -> int:
        # try to send data
        error = None
        sent = -1
        try:
            sent = self._send(data=data, target=target)
            if sent == -1:
                error = IOError('failed to send: %d byte(s) to %s' % (len(data), target))
                # self.__close_channel()
        except socket.error as e:
            error = e
            self.__close_channel()
        # callback
        delegate = self.delegate
        if delegate is not None:
            # get local address as source
            source = self._local
            if source is None:
                sock = self.__channel
                if sock is not None:
                    source = sock.local_address
            if error is None:
                delegate.connection_sent(data=data, source=source, destination=target, connection=self)
            else:
                delegate.connection_error(error=error, data=data, source=source, destination=target, connection=self)
        return sent

    #
    #   States
    #

    @property  # Override
    def state(self) -> ConnectionState:
        return self.__fsm.current_state

    # Override
    def tick(self):
        # drive state machine forward
        self.__fsm.tick()

    def start(self):
        self.__fsm.start()

    def stop(self):
        self.__close_channel()
        self.__fsm.stop()

    #
    #   StateDelegate
    #

    # Override
    def enter_state(self, state: ConnectionState, ctx: StateMachine):
        pass

    # Override
    def exit_state(self, state: ConnectionState, ctx: StateMachine):
        current = ctx.current_state
        if current == ConnectionState.READY:
            if state != ConnectionState.MAINTAINING:
                # change state to 'connected', reset times to just expired
                timestamp = int(time.time()) - self.EXPIRES - 1
                self.__last_sent_time = timestamp
                self.__last_received_time = timestamp
        # callback
        delegate = self.delegate
        if delegate is not None:
            delegate.connection_state_changed(previous=state, current=current, connection=self)

    # Override
    def pause_state(self, state: ConnectionState, ctx: StateMachine):
        pass

    # Override
    def resume_state(self, state: ConnectionState, ctx: StateMachine):
        pass
