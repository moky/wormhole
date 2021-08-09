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

import weakref
from abc import ABC

from ..fsm import Context, BaseTransition, BaseState, BaseMachine

from .connection import Connection


"""
    Finite States:

            //===============\\          (Sent)          //==============\\
            ||               || -----------------------> ||              ||
            ||    Default    ||                          ||  Connecting  ||
            || (Not Connect) || <----------------------- ||              ||
            \\===============//         (Timeout)        \\==============//
                                                              |       |
            //===============\\                               |       |
            ||               || <-----------------------------+       |
            ||     Error     ||          (Error)                 (Received)
            ||               || <-----------------------------+       |
            \\===============//                               |       |
                A       A                                     |       |
                |       |            //===========\\          |       |
                (Error) +----------- ||           ||          |       |
                |                    ||  Expired  || <--------+       |
                |       +----------> ||           ||          |       |
                |       |            \\===========//          |       |
                |       (Timeout)           |         (Timeout)       |
                |       |                   |                 |       V
            //===============\\     (Sent)  |            //==============\\
            ||               || <-----------+            ||              ||
            ||  Maintaining  ||                          ||  Connected   ||
            ||               || -----------------------> ||              ||
            \\===============//       (Received)         \\==============//
"""


class StateMachine(BaseMachine, Context):

    def __init__(self, connection: Connection):
        super().__init__(default=ConnectionState.DEFAULT)
        self.__connection = weakref.ref(connection)
        # init states
        self.__set_state(state=get_default_state())
        self.__set_state(state=get_connecting_state())
        self.__set_state(state=get_connected_state())
        self.__set_state(state=get_expired_state())
        self.__set_state(state=get_maintaining_state())
        self.__set_state(state=get_error_state())

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
            CONNECTING  - sent 'PING', waiting for response
            CONNECTED   - got response recently
            EXPIRED     - long time, needs maintaining (still connected)
            MAINTAINING - sent 'PING', waiting for response
            ERROR       - long long time no response, connection lost
    """

    DEFAULT = 'default'
    CONNECTING = 'connecting'
    CONNECTED = 'connected'
    MAINTAINING = 'maintaining'
    EXPIRED = 'expired'
    ERROR = 'error'

    def __init__(self, name: str):
        super(ConnectionState, self).__init__()
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name

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
        pass

    def on_exit(self, ctx: StateMachine):
        pass

    def on_pause(self, ctx: StateMachine):
        pass

    def on_resume(self, ctx: StateMachine):
        pass


#
#   Default State
#
def get_default_state() -> ConnectionState:
    """ Connection not started yet """
    state = ConnectionState(name=ConnectionState.DEFAULT)
    state.add_transition(transition=DefaultConnectingTransition(target=ConnectionState.CONNECTING))
    return state


class DefaultConnectingTransition(StateTransition):
    """ Default -> Connecting """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection started? change state to 'connecting'
        return conn is not None and conn.opened


#
#   Connecting State
#
def get_connecting_state() -> ConnectionState:
    """ Connection started, not connected yet """
    state = ConnectionState(name=ConnectionState.CONNECTING)
    state.add_transition(transition=ConnectingConnectedTransition(target=ConnectionState.CONNECTED))
    state.add_transition(transition=ConnectingDefaultTransition(target=ConnectionState.DEFAULT))
    return state


class ConnectingConnectedTransition(StateTransition):
    """ Connecting -> Connected """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection connected, change state to 'connected'
        return conn is not None and conn.opened and conn.connected


class ConnectingDefaultTransition(StateTransition):
    """ Connecting -> Default """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection stopped, change state to 'not_connect'
        return conn is None or not conn.opened


#
#   Connected State
#
def get_connected_state() -> ConnectionState:
    """ Normal state of connection """
    state = ConnectionState(name=ConnectionState.CONNECTED)
    state.add_transition(transition=ConnectedExpiredTransition(target=ConnectionState.EXPIRED))
    state.add_transition(transition=ConnectedErrorTransition(target=ConnectionState.ERROR))
    return state


class ConnectedExpiredTransition(StateTransition):
    """ Connected -> Expired """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        from .base_conn import BaseConnection
        assert isinstance(conn, BaseConnection), 'connection error: %s' % conn
        # connection still alive, but
        # long time no response, change state to 'maintain_expired'
        return conn is not None and conn.opened and conn.connected and not conn.received_recently


class ConnectedErrorTransition(StateTransition):
    """ Connected -> Error """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection lost, change state to 'error
        return conn is None or not conn.opened


#
#   Expired State
#
def get_expired_state() -> ConnectionState:
    """ Long time no response, need maintaining """
    state = ConnectionState(name=ConnectionState.EXPIRED)
    state.add_transition(transition=ExpiredMaintainingTransition(target=ConnectionState.MAINTAINING))
    state.add_transition(transition=ExpiredErrorTransition(target=ConnectionState.ERROR))
    return state


class ExpiredMaintainingTransition(StateTransition):
    """ Expired -> Maintaining """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        from .base_conn import BaseConnection
        assert isinstance(conn, BaseConnection), 'connection error: %s' % conn
        # connection still alive, and
        # sent recently, change state to 'maintaining'
        return conn is not None and conn.opened and conn.connected and conn.sent_recently


class ExpiredErrorTransition(StateTransition):
    """ Expired -> Error """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection lost, change state to 'error
        return conn is None or not conn.opened


#
#   Maintaining State
#
def get_maintaining_state() -> ConnectionState:
    """ Heartbeat sent, waiting response """
    state = ConnectionState(name=ConnectionState.MAINTAINING)
    state.add_transition(transition=MaintainingConnectedTransition(target=ConnectionState.CONNECTED))
    state.add_transition(transition=MaintainingExpiredTransition(target=ConnectionState.EXPIRED))
    state.add_transition(transition=MaintainingErrorTransition(target=ConnectionState.ERROR))
    return state


class MaintainingConnectedTransition(StateTransition):
    """ Maintaining -> Connected """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        from .base_conn import BaseConnection
        assert isinstance(conn, BaseConnection), 'connection error: %s' % conn
        # connection still alive, and
        # received recently, change state to 'connected
        return conn is not None and conn.opened and conn.connected and conn.received_recently


class MaintainingExpiredTransition(StateTransition):
    """ Maintaining -> Expired """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        from .base_conn import BaseConnection
        assert isinstance(conn, BaseConnection), 'connection error: %s' % conn
        # connection still alive, but
        # long time no sending, change state to 'maintain_expired'
        return conn is not None and conn.opened and conn.connected and not conn.sent_recently


class MaintainingErrorTransition(StateTransition):
    """ Maintaining -> Error """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        from .base_conn import BaseConnection
        assert isinstance(conn, BaseConnection), 'connection error: %s' % conn
        # connection lost, or
        # long long time no response, change state to 'error'
        return conn is None or not conn.opened or conn.long_time_not_received


#
#   Error State
#
def get_error_state() -> ConnectionState:
    """ Connection lost """
    state = ConnectionState(name=ConnectionState.ERROR)
    state.add_transition(transition=ErrorDefaultTransition(target=ConnectionState.DEFAULT))
    return state


class ErrorDefaultTransition(StateTransition):
    """ Error -> Default """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection reset, change state to 'not_connect'
        return conn is not None and conn.opened
