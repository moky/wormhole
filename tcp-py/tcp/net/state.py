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
        builder = self._create_state_builder()
        self.__set_state(state=builder.get_default_state())
        self.__set_state(state=builder.get_connecting_state())
        self.__set_state(state=builder.get_connected_state())
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
        # Default -> Connecting
        state.add_transition(transition=builder.get_default_connecting_transition())
        return state

    # Connection started, not connected yet
    def get_connecting_state(self) -> ConnectionState:
        builder = self.__builder
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.CONNECTING)
        # Connecting -> Connected
        state.add_transition(transition=builder.get_connecting_connected_transition())
        # Connecting -> Default
        state.add_transition(transition=builder.get_connecting_default_transition())
        return state

    # Normal state of connection
    def get_connected_state(self) -> ConnectionState:
        builder = self.__builder
        # assert isinstance(builder, TransitionBuilder)
        state = self.get_named_state(name=ConnectionState.CONNECTED)
        # Connected -> Expired
        state.add_transition(transition=builder.get_connected_expired_transition())
        # Connected -> Error
        state.add_transition(transition=builder.get_connected_error_transition())
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
        # Maintaining -> Connected
        state.add_transition(transition=builder.get_maintaining_connected_transition())
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
    def get_default_connecting_transition(self):
        return DefaultConnectingTransition(target=ConnectionState.CONNECTING)

    # Connecting

    # noinspection PyMethodMayBeStatic
    def get_connecting_connected_transition(self):
        return ConnectingConnectedTransition(target=ConnectionState.CONNECTED)

    # noinspection PyMethodMayBeStatic
    def get_connecting_default_transition(self):
        return ConnectingDefaultTransition(target=ConnectionState.DEFAULT)

    # Connected

    # noinspection PyMethodMayBeStatic
    def get_connected_expired_transition(self):
        return ConnectedExpiredTransition(target=ConnectionState.EXPIRED)

    # noinspection PyMethodMayBeStatic
    def get_connected_error_transition(self):
        return ConnectedErrorTransition(target=ConnectionState.ERROR)

    # Expired

    # noinspection PyMethodMayBeStatic
    def get_expired_maintaining_transition(self):
        return ExpiredMaintainingTransition(target=ConnectionState.MAINTAINING)

    # noinspection PyMethodMayBeStatic
    def get_expired_error_transition(self):
        return ExpiredErrorTransition(target=ConnectionState.ERROR)

    # Maintaining

    # noinspection PyMethodMayBeStatic
    def get_maintaining_connected_transition(self):
        return MaintainingConnectedTransition(target=ConnectionState.CONNECTED)

    # noinspection PyMethodMayBeStatic
    def get_maintaining_expired_transition(self):
        return MaintainingExpiredTransition(target=ConnectionState.EXPIRED)

    # noinspection PyMethodMayBeStatic
    def get_maintaining_error_transition(self):
        return MaintainingErrorTransition(target=ConnectionState.ERROR)

    # Error

    # noinspection PyMethodMayBeStatic
    def get_error_default_transition(self) -> StateTransition:
        return ErrorDefaultTransition(target=ConnectionState.DEFAULT)


#
#   Transitions
#

class DefaultConnectingTransition(StateTransition):
    """ Default -> Connecting """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection started? change state to 'connecting'
        return conn is not None and conn.opened


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


class ErrorDefaultTransition(StateTransition):
    """ Error -> Default """

    def evaluate(self, ctx: StateMachine) -> bool:
        conn = ctx.connection
        # connection reset, change state to 'not_connect'
        return conn is not None and conn.opened
