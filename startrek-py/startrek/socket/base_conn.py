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

from ..types import SocketAddress, AddressPairObject
from ..fsm import Delegate as StateDelegate

from ..net import Hub
from ..net import Channel
from ..net import Connection, ConnectionState
from ..net import ConnectionDelegate
from ..net.state import StateMachine, StateOrder, TimedConnection


class BaseConnection(AddressPairObject, Connection, TimedConnection, StateDelegate):

    EXPIRES = 16  # seconds

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress]):
        super().__init__(remote=remote, local=local)
        self.__delegate_ref = None
        self.__channel_ref = None
        # active times
        self.__last_sent_time = 0
        self.__last_received_time = 0
        # Finite State Machine
        self.__fsm: Optional[StateMachine] = None

    #
    #   Connection Event Handler
    #

    @property
    def delegate(self) -> ConnectionDelegate:
        """ Delegate for handling connection events """
        ref = self.__delegate_ref
        if ref is not None:
            return ref()

    @delegate.setter
    def delegate(self, gate: ConnectionDelegate):
        self.__delegate_ref = None if gate is None else weakref.ref(gate)

    #
    #   State Machine
    #

    @property  # protected
    def fsm(self) -> Optional[StateMachine]:
        return self.__fsm

    # private
    async def _set_state_machine(self, fsm: Optional[StateMachine]):
        # 1. replace with new machine
        old = self.__fsm
        self.__fsm = fsm
        # 2. stop old machine
        if old is not None and old is not fsm:
            await old.stop()

    def _create_state_machine(self) -> StateMachine:
        fsm = StateMachine(connection=self)
        fsm.delegate = self
        return fsm

    #
    #   Channel
    #

    @property
    def channel(self) -> Optional[Channel]:
        ref = self.__channel_ref
        if ref is not None:
            return ref()

    async def _set_channel(self, channel: Optional[Channel]):
        # 1. replace with new channel
        old = self.channel
        if channel is not None:
            self.__channel_ref = weakref.ref(channel)
        # else:
        #     self.__channel_ref = None
        # 2. close old channel
        if old is not None and old is not channel:
            await old.close()

    #
    #   Flags
    #

    @property  # Override
    def closed(self) -> bool:
        if self.__channel_ref is None:
            # initializing
            return False
        channel = self.channel
        return channel is None or channel.closed

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
        return (not self.closed) and (self.connected or self.bound)

    @property
    def available(self) -> bool:
        channel = self.channel
        return channel is not None and channel.available

    @property
    def vacant(self) -> bool:
        channel = self.channel
        return channel is not None and channel.vacant

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s">\n%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.channel, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s">\n%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.channel, cname, mod)

    # Override
    async def close(self):
        # stop state machine
        await self._set_state_machine(fsm=None)
        # close channel
        await self._set_channel(channel=None)

    async def start(self, hub: Hub):
        """ Get channel from hub """
        # 1. get channel from hub
        await self._open_channel(hub=hub)
        # 2. start state machine
        await self._start_machine()

    async def _start_machine(self):
        fsm = self._create_state_machine()
        await self._set_state_machine(fsm=fsm)
        await fsm.start()

    # protected
    async def _open_channel(self, hub: Hub) -> Optional[Channel]:
        sock = await hub.open(remote=self.remote_address, local=self.local_address)
        if sock is None:
            assert False, 'failed to open channel: remote=%s, local=%s' % (self.remote_address, self.local_address)
        else:
            await self._set_channel(channel=sock)
        return sock

    #
    #   I/O
    #

    # Override
    async def received(self, data: bytes):
        self.__last_received_time = time.time()  # update received time
        delegate = self.delegate
        if delegate is not None:
            await delegate.connection_received(data=data, connection=self)

    async def _send(self, data: bytes, target: Optional[SocketAddress]) -> int:
        channel = self.channel
        if channel is None or not channel.alive:
            # raise socket.error('socket channel lost: %s' % channel)
            return -1
        elif target is None:
            # assert False, 'target address empty'
            return -1
        sent = await channel.send(data=data, target=target)
        if sent > 0:
            # update sent time
            self.__last_sent_time = time.time()
        return sent

    # Override
    async def send(self, data: bytes) -> int:
        # try to send data
        error = None
        sent = -1
        try:
            sent = await self._send(data=data, target=self.remote_address)
            if sent < 0:  # == -1:
                raise socket.error('failed to send: %d byte(s) to %s' % (len(data), self.remote_address))
        except socket.error as e:
            error = e
            # socket error, close current channel
            await self._set_channel(channel=None)
        # callback
        delegate = self.delegate
        if delegate is not None:
            if error is None:
                await delegate.connection_sent(sent=sent, data=data, connection=self)
            else:
                await delegate.connection_failed(error=error, data=data, connection=self)
        return sent

    #
    #   States
    #

    @property  # Override
    def state(self) -> Optional[ConnectionState]:
        fsm = self.fsm
        if fsm is not None:
            return fsm.current_state

    # Override
    async def tick(self, now: float, elapsed: float):
        if self.__channel_ref is None:
            # not initialized
            return
        fsm = self.fsm
        if fsm is not None:
            # drive state machine forward
            await fsm.tick(now=now, elapsed=elapsed)

    #
    #   Timed Connection
    #

    @property  # Override
    def last_sent_time(self) -> float:
        return self.__last_sent_time

    @property  # Override
    def last_received_time(self) -> float:
        return self.__last_received_time

    # Override
    def is_sent_recently(self, now: float) -> bool:
        return now <= self.__last_sent_time + self.EXPIRES

    # Override
    def is_received_recently(self, now: float) -> bool:
        return now <= self.__last_received_time + self.EXPIRES

    # Override
    def is_not_received_long_time_ago(self, now: float) -> bool:
        return now > self.__last_received_time + (self.EXPIRES << 3)

    #
    #   StateDelegate
    #

    # Override
    async def enter_state(self, state: Optional[ConnectionState], ctx: StateMachine, now: float):
        pass

    # Override
    async def exit_state(self, state: Optional[ConnectionState], ctx: StateMachine, now: float):
        current = ctx.current_state
        if isinstance(current, ConnectionState):
            index = current.index
        else:
            assert current is None, 'unknown connection state: %s' % current
            index = -1
        # if current == 'ready'
        if index == StateOrder.READY:
            previous = -1 if state is None else state.index
            # if preparing == 'preparing'
            if previous == StateOrder.PREPARING:
                # connection state changed from 'preparing' to 'ready',
                # set times to expired soon.
                timestamp = time.time() - (self.EXPIRES >> 1)
                if self.__last_sent_time < timestamp:
                    self.__last_sent_time = timestamp
                if self.__last_received_time < timestamp:
                    self.__last_received_time = timestamp
        # callback
        delegate = self.delegate
        if delegate is not None:
            await delegate.connection_state_changed(previous=state, current=current, connection=self)

    # Override
    async def pause_state(self, state: Optional[ConnectionState], ctx: StateMachine, now: float):
        pass

    # Override
    async def resume_state(self, state: Optional[ConnectionState], ctx: StateMachine, now: float):
        pass
