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

import time
import weakref
from abc import ABC, abstractmethod

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

    def __init__(self, connection: Connection):
        super().__init__(default=ConnectionState.DEFAULT)
        self.__connection = weakref.ref(connection)
        # init states
        builder = self._create_state_builder()
        self.__set_state(state=builder.get_default_state())
        self.__set_state(state=builder.get_preparing_state())
        self.__set_state(state=builder.get_ready_state())
        self.__set_state(state=builder.get_expired_state())
        self.__set_state(state=builder.get_maintaining_state())
        self.__set_state(state=builder.get_error_state())

    # noinspection PyMethodMayBeStatic
    def _create_state_builder(self):
        return StateBuilder(transition_builder=TransitionBuilder())

    def __set_state(self, state):
        self.add_state(name=state.name, state=state)

    @property
    def context(self) -> Context:
        return self

    @property
    def connection(self) -> Connection:
        return self.__connection()


class StateTransition(BaseTransition[StateMachine], ABC):
    pass


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

    DEFAULT = 'default'
    PREPARING = 'preparing'
    READY = 'ready'
    MAINTAINING = 'maintaining'
    EXPIRED = 'expired'
    ERROR = 'error'

    def __init__(self, name: str):
        super(ConnectionState, self).__init__()
        self.__name = name
        self.__time = 0  # enter time

    @property
    def name(self) -> str:
        return self.__name

    @property
    def enter_time(self) -> int:
        return self.__time

    def __str__(self) -> str:
        return self.__name

    def __repr__(self) -> str:
        return self.__name

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        elif isinstance(other, ConnectionState):
            return self.__name == other.name
        elif isinstance(other, str):
            return self.__name == other
        else:
            return False

    def __ne__(self, other) -> bool:
        if self is other:
            return False
        elif isinstance(other, ConnectionState):
            return self.__name != other.name
        elif isinstance(other, str):
            return self.__name != other
        else:
            return True

    def on_enter(self, ctx: StateMachine):
        self.__time = int(time.time())

    def on_exit(self, ctx: StateMachine):
        self.__time = 0

    def on_pause(self, ctx: StateMachine):
        pass

    def on_resume(self, ctx: StateMachine):
        pass


class TimedConnection(ABC):

    @property
    def last_sent_time(self) -> int:
        raise NotImplemented

    @property
    def last_received_time(self) -> int:
        raise NotImplemented

    @abstractmethod
    def is_sent_recently(self, now: int) -> bool:
        raise NotImplemented

    @abstractmethod
    def is_received_recently(self, now: int) -> bool:
        raise NotImplemented

    @abstractmethod
    def is_long_time_not_received(self, now: int) -> bool:
        raise NotImplemented


#
#   Builders
#

class StateBuilder:

    def __init__(self, transition_builder):
        super().__init__()
        self.__builder = transition_builder

    # noinspection PyMethodMayBeStatic
    def get_named_state(self, name: str) -> ConnectionState:
        return ConnectionState(name=name)

    # Connection not started yet
    def get_default_state(self) -> ConnectionState:
        builder = self.__builder
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.DEFAULT)
        # Default -> Preparing
        state.add_transition(transition=builder.get_default_preparing_transition())
        return state

    # Connection started, preparing to connect/bind
    def get_preparing_state(self) -> ConnectionState:
        builder = self.__builder
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.PREPARING)
        # Preparing -> Ready
        state.add_transition(transition=builder.get_preparing_ready_transition())
        # Preparing -> Default
        state.add_transition(transition=builder.get_preparing_default_transition())
        return state

    # Normal state of connection
    def get_ready_state(self) -> ConnectionState:
        builder = self.__builder
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.READY)
        # Ready -> Expired
        state.add_transition(transition=builder.get_ready_expired_transition())
        # Ready -> Error
        state.add_transition(transition=builder.get_ready_error_transition())
        return state

    # Long time no response, need maintaining
    def get_expired_state(self) -> ConnectionState:
        builder = self.__builder
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.EXPIRED)
        # Expired -> Maintaining
        state.add_transition(transition=builder.get_expired_maintaining_transition())
        # Expired -> Error
        state.add_transition(transition=builder.get_expired_error_transition())
        return state

    # Heartbeat sent, waiting response
    def get_maintaining_state(self) -> ConnectionState:
        builder = self.__builder
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.MAINTAINING)
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
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.ERROR)
        # Error -> Default
        state.add_transition(transition=builder.get_error_default_transition())
        return state


class TransitionBuilder:

    # noinspection PyMethodMayBeStatic
    def get_default_preparing_transition(self):
        return DefaultPreparingTransition(target=ConnectionState.PREPARING)

    # Preparing

    # noinspection PyMethodMayBeStatic
    def get_preparing_ready_transition(self):
        return PreparingReadyTransition(target=ConnectionState.READY)

    # noinspection PyMethodMayBeStatic
    def get_preparing_default_transition(self):
        return PreparingDefaultTransition(target=ConnectionState.DEFAULT)

    # Ready

    # noinspection PyMethodMayBeStatic
    def get_ready_expired_transition(self):
        return ReadyExpiredTransition(target=ConnectionState.EXPIRED)

    # noinspection PyMethodMayBeStatic
    def get_ready_error_transition(self):
        return ReadyErrorTransition(target=ConnectionState.ERROR)

    # Expired

    # noinspection PyMethodMayBeStatic
    def get_expired_maintaining_transition(self):
        return ExpiredMaintainingTransition(target=ConnectionState.MAINTAINING)

    # noinspection PyMethodMayBeStatic
    def get_expired_error_transition(self):
        return ExpiredErrorTransition(target=ConnectionState.ERROR)

    # Maintaining

    # noinspection PyMethodMayBeStatic
    def get_maintaining_ready_transition(self):
        return MaintainingReadyTransition(target=ConnectionState.READY)

    # noinspection PyMethodMayBeStatic
    def get_maintaining_expired_transition(self):
        return MaintainingExpiredTransition(target=ConnectionState.EXPIRED)

    # noinspection PyMethodMayBeStatic
    def get_maintaining_error_transition(self):
        return MaintainingErrorTransition(target=ConnectionState.ERROR)

    # noinspection PyMethodMayBeStatic
    def get_error_default_transition(self):
        return ErrorDefaultTransition(target=ConnectionState.DEFAULT)


#
#   Transitions
#

class DefaultPreparingTransition(StateTransition):
    """ Default -> Preparing """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection started? change state to 'preparing'
        return conn is not None and conn.opened


class PreparingReadyTransition(StateTransition):
    """ Preparing -> Ready """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connected or bound, change state to 'ready'
        return conn is not None and conn.alive


class PreparingDefaultTransition(StateTransition):
    """ Preparing -> Default """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection stopped, change state to 'not_connect'
        return conn is None or not conn.opened


class ReadyExpiredTransition(StateTransition):
    """ Ready -> Expired """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, but
        # long time no response, change state to 'maintain_expired'
        return not conn.is_received_recently(now=int(time.time()))


class ReadyErrorTransition(StateTransition):
    """ Ready -> Error """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection lost, change state to 'error
        return conn is None or not conn.opened


class ExpiredMaintainingTransition(StateTransition):
    """ Expired -> Maintaining """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, and
        # sent recently, change state to 'maintaining'
        return conn.is_sent_recently(now=int(time.time()))


class ExpiredErrorTransition(StateTransition):
    """ Expired -> Error """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection lost, change state to 'error
        return conn is None or not conn.opened


class MaintainingReadyTransition(StateTransition):
    """ Maintaining -> Ready """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, and
        # received recently, change state to 'connected
        return conn.is_received_recently(now=int(time.time()))


class MaintainingExpiredTransition(StateTransition):
    """ Maintaining -> Expired """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, but
        # long time no sending, change state to 'maintain_expired'
        return not conn.is_sent_recently(now=int(time.time()))


class MaintainingErrorTransition(StateTransition):
    """ Maintaining -> Error """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection lost, change state to 'error'
        if conn is None or not conn.opened:
            return True
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # long time no response, change state to 'error'
        return conn.is_long_time_not_received(now=int(time.time()))


class ErrorDefaultTransition(StateTransition):
    """ Error -> Default """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        if conn is None or not conn.alive:
            return False
        assert isinstance(conn, TimedConnection), 'connection error: %s' % conn
        # connection still alive, and
        # can sent/receive data during this state
        current = ctx.current_state
        assert isinstance(current, ConnectionState), 'connection state error: %s' % current
        enter = current.enter_time
        if enter > 0:
            return conn.last_sent_time > enter or conn.last_received_time > enter
