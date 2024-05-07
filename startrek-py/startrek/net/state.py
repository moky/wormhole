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

import weakref
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Union

from ..fsm import Context, BaseTransition, BaseState, BaseMachine

from .connection import Connection


"""
    Finite States:

            //===============\\          (Start)          //=============\\
            ||               || ------------------------> ||             ||
            ||    Default    ||                           ||  Preparing  ||
            ||               || <------------------------ ||             ||
            \\===============//         (Timeout)         \\=============//
                                                              |       |
            //===============\\                               |       |
            ||               || <-----------------------------+       |
            ||     Error     ||          (Error)                 (Connected
            ||               || <-----------------------------+   or bound)
            \\===============//                               |       |
                A       A                                     |       |
                |       |            //===========\\          |       |
                (Error) +----------- ||           ||          |       |
                |                    ||  Expired  || <--------+       |
                |       +----------> ||           ||          |       |
                |       |            \\===========//          |       |
                |       (Timeout)           |         (Timeout)       |
                |       |                   |                 |       V
            //===============\\     (Sent)  |             //=============\\
            ||               || <-----------+             ||             ||
            ||  Maintaining  ||                           ||    Ready    ||
            ||               || ------------------------> ||             ||
            \\===============//       (Received)          \\=============//
"""


class StateMachine(BaseMachine, Context):
    """ Connection State Machine """

    def __init__(self, connection: Connection):
        super().__init__()
        self.__conn_ref = weakref.ref(connection)
        # init states
        builder = self._create_state_builder()
        self.add_state(state=builder.get_default_state())
        self.add_state(state=builder.get_preparing_state())
        self.add_state(state=builder.get_ready_state())
        self.add_state(state=builder.get_expired_state())
        self.add_state(state=builder.get_maintaining_state())
        self.add_state(state=builder.get_error_state())

    # noinspection PyMethodMayBeStatic
    def _create_state_builder(self):
        return StateBuilder(transition_builder=TransitionBuilder())

    @property  # Override
    def context(self) -> Context:
        return self

    @property
    def connection(self) -> Connection:
        return self.__conn_ref()


class StateOrder(IntEnum):
    """ Connection State Order """
    INIT = 0  # default
    PREPARING = 1
    READY = 2
    MAINTAINING = 3
    EXPIRED = 4
    ERROR = 5


class StateTransition(BaseTransition[StateMachine], ABC):
    """ Connection State Transition """

    def __init__(self, target: Union[int, StateOrder]):
        if isinstance(target, StateOrder):
            target = target.value
        super().__init__(target=target)

    @abstractmethod  # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        raise NotImplemented


class ConnectionState(BaseState[StateMachine, StateTransition]):
    """
        Connection State
        ~~~~~~~~~~~~~~~~

        Defined for indicating connection status

            DEFAULT     - 'initialized', or sent timeout
            PREPARING   - connecting or binding
            READY       - got response recently
            EXPIRED     - long time, needs maintaining (still connected)
            MAINTAINING - sent 'PING', waiting for response
            ERROR       - long long time no response, connection lost
    """

    def __init__(self, order: StateOrder):
        super().__init__(index=order.value)
        self.__name = str(order)
        self.__time = 0  # enter time

    @property
    def name(self) -> str:
        return self.__name

    @property
    def enter_time(self) -> float:
        return self.__time

    def __str__(self) -> str:
        return self.__name

    def __repr__(self) -> str:
        return self.__name

    def __eq__(self, other) -> bool:
        if isinstance(other, ConnectionState):
            if self is other:
                return True
            return self.index == other.index
        elif isinstance(other, StateOrder):
            return self.index == other.value
        elif isinstance(other, int):
            return self.index == other
        elif isinstance(other, str):
            return self.__name == other
        else:
            return False

    def __ne__(self, other) -> bool:
        if isinstance(other, ConnectionState):
            if self is other:
                return False
            return self.index != other.index
        elif isinstance(other, StateOrder):
            return self.index != other.value
        elif isinstance(other, int):
            return self.index != other
        elif isinstance(other, str):
            return self.__name != other
        else:
            return True

    # Override
    async def on_enter(self, old, ctx: StateMachine, now: float):
        self.__time = now

    # Override
    async def on_exit(self, new, ctx: StateMachine, now: float):
        self.__time = 0

    # Override
    async def on_pause(self, ctx: StateMachine, now: float):
        pass

    # Override
    async def on_resume(self, ctx: StateMachine, now: float):
        pass


class TimedConnection(ABC):

    @property
    @abstractmethod
    def last_sent_time(self) -> float:
        raise NotImplemented

    @property
    @abstractmethod
    def last_received_time(self) -> float:
        raise NotImplemented

    @abstractmethod
    def is_sent_recently(self, now: float) -> bool:
        raise NotImplemented

    @abstractmethod
    def is_received_recently(self, now: float) -> bool:
        raise NotImplemented

    @abstractmethod
    def is_not_received_long_time_ago(self, now: float) -> bool:
        raise NotImplemented


#
#   Builders
#

class StateBuilder:

    def __init__(self, transition_builder):
        super().__init__()
        self.__builder: TransitionBuilder = transition_builder

    # Connection not started yet
    def get_default_state(self) -> ConnectionState:
        builder = self.__builder
        state = ConnectionState(order=StateOrder.INIT)
        # Default -> Preparing
        state.add_transition(transition=builder.get_default_preparing_transition())
        return state

    # Connection started, preparing to connect/bind
    def get_preparing_state(self) -> ConnectionState:
        builder = self.__builder
        state = ConnectionState(order=StateOrder.PREPARING)
        # Preparing -> Ready
        state.add_transition(transition=builder.get_preparing_ready_transition())
        # Preparing -> Default
        state.add_transition(transition=builder.get_preparing_default_transition())
        return state

    # Normal state of connection
    def get_ready_state(self) -> ConnectionState:
        builder = self.__builder
        state = ConnectionState(order=StateOrder.READY)
        # Ready -> Expired
        state.add_transition(transition=builder.get_ready_expired_transition())
        # Ready -> Error
        state.add_transition(transition=builder.get_ready_error_transition())
        return state

    # Long time no response, need maintaining
    def get_expired_state(self) -> ConnectionState:
        builder = self.__builder
        state = ConnectionState(order=StateOrder.EXPIRED)
        # Expired -> Maintaining
        state.add_transition(transition=builder.get_expired_maintaining_transition())
        # Expired -> Error
        state.add_transition(transition=builder.get_expired_error_transition())
        return state

    # Heartbeat sent, waiting response
    def get_maintaining_state(self) -> ConnectionState:
        builder = self.__builder
        state = ConnectionState(order=StateOrder.MAINTAINING)
        # Maintaining -> Ready
        state.add_transition(transition=builder.get_maintaining_ready_transition())
        # Maintaining -> Expired
        state.add_transition(transition=builder.get_maintaining_expired_transition())
        # Maintaining -> Error
        state.add_transition(transition=builder.get_maintaining_error_transition())
        return state

    # Connection lost
    def get_error_state(self) -> ConnectionState:
        builder = self.__builder
        state = ConnectionState(order=StateOrder.ERROR)
        # Error -> Default
        state.add_transition(transition=builder.get_error_default_transition())
        return state


class TransitionBuilder:

    # noinspection PyMethodMayBeStatic
    def get_default_preparing_transition(self):
        return DefaultPreparingTransition(target=StateOrder.PREPARING)

    # Preparing

    # noinspection PyMethodMayBeStatic
    def get_preparing_ready_transition(self):
        return PreparingReadyTransition(target=StateOrder.READY)

    # noinspection PyMethodMayBeStatic
    def get_preparing_default_transition(self):
        return PreparingDefaultTransition(target=StateOrder.INIT)

    # Ready

    # noinspection PyMethodMayBeStatic
    def get_ready_expired_transition(self):
        return ReadyExpiredTransition(target=StateOrder.EXPIRED)

    # noinspection PyMethodMayBeStatic
    def get_ready_error_transition(self):
        return ReadyErrorTransition(target=StateOrder.ERROR)

    # Expired

    # noinspection PyMethodMayBeStatic
    def get_expired_maintaining_transition(self):
        return ExpiredMaintainingTransition(target=StateOrder.MAINTAINING)

    # noinspection PyMethodMayBeStatic
    def get_expired_error_transition(self):
        return ExpiredErrorTransition(target=StateOrder.ERROR)

    # Maintaining

    # noinspection PyMethodMayBeStatic
    def get_maintaining_ready_transition(self):
        return MaintainingReadyTransition(target=StateOrder.READY)

    # noinspection PyMethodMayBeStatic
    def get_maintaining_expired_transition(self):
        return MaintainingExpiredTransition(target=StateOrder.EXPIRED)

    # noinspection PyMethodMayBeStatic
    def get_maintaining_error_transition(self):
        return MaintainingErrorTransition(target=StateOrder.ERROR)

    # noinspection PyMethodMayBeStatic
    def get_error_default_transition(self):
        return ErrorDefaultTransition(target=StateOrder.INIT)


#
#   Transitions
#

class DefaultPreparingTransition(StateTransition):
    """ Default -> Preparing """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        # connection started? change state to 'preparing'
        return not (conn is None or conn.closed)


class PreparingReadyTransition(StateTransition):
    """ Preparing -> Ready """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        # connected or bound, change state to 'ready'
        return conn is not None and conn.alive


class PreparingDefaultTransition(StateTransition):
    """ Preparing -> Default """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        # connection stopped, change state to 'not_connect'
        return conn is None or conn.closed


class ReadyExpiredTransition(StateTransition):
    """ Ready -> Expired """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, but
        # long time no response, change state to 'maintain_expired'
        return not conn.is_received_recently(now=now)


class ReadyErrorTransition(StateTransition):
    """ Ready -> Error """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        # connection lost, change state to 'error
        return conn is None or not conn.alive


class ExpiredMaintainingTransition(StateTransition):
    """ Expired -> Maintaining """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, and
        # sent recently, change state to 'maintaining'
        return conn.is_sent_recently(now=now)


class ExpiredErrorTransition(StateTransition):
    """ Expired -> Error """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return True
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection lost, or
        # long time no response, change state to 'error'
        return conn.is_not_received_long_time_ago(now=now)


class MaintainingReadyTransition(StateTransition):
    """ Maintaining -> Ready """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, and
        # received recently, change state to 'ready'
        return conn.is_received_recently(now=now)


class MaintainingExpiredTransition(StateTransition):
    """ Maintaining -> Expired """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, but
        # long time no sending, change state to 'maintain_expired'
        return not conn.is_sent_recently(now=now)


class MaintainingErrorTransition(StateTransition):
    """ Maintaining -> Error """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        # connection lost, change state to 'error'
        if conn is None or not conn.alive:
            return True
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection lost, or
        # long time no response, change state to 'error'
        return conn.is_not_received_long_time_ago(now=now)


class ErrorDefaultTransition(StateTransition):
    """ Error -> Default """

    # Override
    def evaluate(self, ctx: StateMachine, now: float) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, and
        # can receive data during this state
        current = ctx.current_state
        assert isinstance(current, ConnectionState), 'connection state error: %s' % current
        enter = current.enter_time
        assert enter > 0, 'should not happen'
        return enter < conn.last_received_time
