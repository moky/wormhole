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

from ..types import Address, AddressPairObject
from ..fsm import StateDelegate

from .hub import Hub
from .channel import Channel
from .connection import Connection
from .delegate import ConnectionDelegate as Delegate
from .state import ConnectionState, StateMachine, TimedConnection


class BaseConnection(AddressPairObject, Connection, TimedConnection, StateDelegate):

    EXPIRES = 16  # seconds

    def __init__(self, remote: Address, local: Optional[Address], channel: Channel, delegate: Delegate, hub: Hub):
        super().__init__(remote=remote, local=local)
        self.__channel_ref = weakref.ref(channel)
        self.__delegate = weakref.ref(delegate)
        self.__hub_ref = weakref.ref(hub)
        # active times
        self.__last_sent_time = 0
        self.__last_received_time = 0
        # Finite State Machine
        self.__fsm = self._create_state_machine()

    def __del__(self):
        # make sure the relative channel is closed
        self._set_channel(channel=None)
        self.__fsm = None

    def _create_state_machine(self) -> StateMachine:
        fsm = StateMachine(connection=self)
        fsm.delegate = self
        return fsm

    @property
    def delegate(self) -> Delegate:
        return self.__delegate()

    @property
    def hub(self) -> Hub:
        return self.__hub_ref()

    @property
    def channel(self) -> Optional[Channel]:
        return self._get_channel()

    def _get_channel(self) -> Optional[Channel]:
        ref = self.__channel_ref
        if ref is not None:
            return ref()

    def _set_channel(self, channel: Optional[Channel]):
        # 1. check old channel
        old = self._get_channel()
        if old is not None and old is not channel:
            # close old channel
            self._close_channel(channel=old)
        # 2. set new channel
        if channel is None:
            self.__channel_ref = None
        else:
            self.__channel_ref = weakref.ref(channel)

    # noinspection PyMethodMayBeStatic
    def _close_channel(self, channel: Channel):
        if channel.opened:
            channel.close()

    @property  # Override
    def opened(self) -> bool:
        if self.__fsm is None:
            # closed
            return False
        channel = self.channel
        return channel is not None and channel.opened

    @property  # Override
    def bound(self) -> bool:
        channel = self.channel
        return channel is not None and channel.bound

    @property  # Override
    def connected(self) -> bool:
        channel = self.channel
        return channel is not None and channel.connected

    @property  # Override
    def alive(self) -> bool:
        # channel = self.channel
        # return channel is not None and channel.alive
        return self.opened and (self.connected or self.bound)

    # Override
    def close(self):
        self._set_channel(channel=None)
        self.__fsm.stop()
        self.__fsm = None

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
    def received(self, data: bytes, remote: Optional[Address], local: Optional[Address]):
        self.__last_received_time = int(time.time())
        delegate = self.delegate
        if delegate is not None:
            delegate.connection_received(data=data, source=remote, destination=local, connection=self)

    def _send(self, data: bytes, target: Optional[Address]) -> int:
        channel = self.channel
        if channel is None or not channel.alive:
            raise socket.error('socket channel lost: %s' % channel)
        sent = channel.send(data=data, target=target)
        if sent > 0:
            self.__last_sent_time = int(time.time())
        return sent

    # Override
    def send(self, data: bytes, target: Optional[Address] = None) -> int:
        # try to send data
        error = None
        sent = -1
        try:
            sent = self._send(data=data, target=target)
            if sent <= 0:  # == -1:
                error = ConnectionError('failed to send: %d byte(s) to %s' % (len(data), target))
        except socket.error as e:
            error = e
            # socket error, close the channel
            self._set_channel(channel=None)
        # callback
        delegate = self.delegate
        if delegate is not None:
            # get local address as source
            source = self._local
            if source is None:
                channel = self._get_channel()
                if channel is not None:
                    source = channel.local_address
            if error is None:
                if sent < len(data):
                    data = data[:sent]
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
        self._set_channel(channel=None)
        self.__fsm.stop()
        self.__fsm = None

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
