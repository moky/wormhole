/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * ==============================================================================
 */
package chat.dim.net;

import java.lang.ref.WeakReference;
import java.util.Date;

import chat.dim.fsm.BaseMachine;
import chat.dim.fsm.BaseTransition;
import chat.dim.fsm.Context;
import chat.dim.fsm.Delegate;

interface StateDelegate extends Delegate<StateMachine, StateTransition, ConnectionState> {

}

abstract class StateTransition extends BaseTransition<StateMachine> {

    protected StateTransition(String target) {
        super(target);
    }
}

class StateMachine extends BaseMachine<StateMachine, StateTransition, ConnectionState>
        implements Context {

    private final WeakReference<BaseConnection> connectionRef;

    public StateMachine(BaseConnection connection) {
        super(ConnectionState.DEFAULT);

        connectionRef = new WeakReference<>(connection);

        // init states
        StateBuilder builder = getStateBuilder();
        setState(builder.getDefaultState());
        setState(builder.getConnectingState());
        setState(builder.getConnectedState());
        setState(builder.getExpiredState());
        setState(builder.getMaintainingState());
        setState(builder.getErrorState());
    }

    protected StateBuilder getStateBuilder() {
        return new StateBuilder(new TransitionBuilder());
    }

    @Override
    protected StateMachine getContext() {
        return this;
    }

    private void setState(ConnectionState state) {
        addState(state.name, state);
    }

    BaseConnection getConnection() {
        return connectionRef.get();
    }
}

class StateBuilder {

    private final TransitionBuilder builder;

    StateBuilder(TransitionBuilder transitionBuilder) {
        super();
        builder = transitionBuilder;
    }

    ConnectionState getNamedState(String name) {
        return new ConnectionState(name);
    }

    // Connection not started yet
    ConnectionState getDefaultState() {
        ConnectionState state = getNamedState(ConnectionState.DEFAULT);
        // Default -> Connecting
        state.addTransition(builder.getDefaultConnectingTransition());
        return state;
    }

    // Connection started, not connected yet
    ConnectionState getConnectingState() {
        ConnectionState state = getNamedState(ConnectionState.CONNECTING);
        // Connecting -> Connected
        state.addTransition(builder.getConnectingConnectedTransition());
        // Connecting -> Default
        state.addTransition(builder.getConnectingDefaultTransition());
        return state;
    }

    // Normal state of connection
    ConnectionState getConnectedState() {
        ConnectionState state = getNamedState(ConnectionState.CONNECTED);
        // Connected -> Expired
        state.addTransition(builder.getConnectedExpiredTransition());
        // Connected -> Error
        state.addTransition(builder.getConnectedErrorTransition());
        return state;
    }

    // Long time no response, need maintaining
    ConnectionState getExpiredState() {
        ConnectionState state = getNamedState(ConnectionState.EXPIRED);
        // Expired -> Maintaining
        state.addTransition(builder.getExpiredMaintainingTransition());
        // Expired -> Error
        state.addTransition(builder.getExpiredErrorTransition());
        return state;
    }

    // Heartbeat sent, waiting response
    ConnectionState getMaintainingState() {
        ConnectionState state = getNamedState(ConnectionState.MAINTAINING);
        // Maintaining -> Connected
        state.addTransition(builder.getMaintainingConnectedTransition());
        // Maintaining -> Expired
        state.addTransition(builder.getMaintainingExpiredTransition());
        // Maintaining -> Error
        state.addTransition(builder.getMaintainingErrorTransition());
        return state;
    }

    // Connection lost
    ConnectionState getErrorState() {
        ConnectionState state = getNamedState(ConnectionState.ERROR);
        // Error -> Default
        state.addTransition(builder.getErrorDefaultTransition());
        return state;
    }
}

class TransitionBuilder {

    // Default -> Connecting
    StateTransition getDefaultConnectingTransition() {
        return new StateTransition(ConnectionState.CONNECTING) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection started? change state to 'connecting'
                return conn != null && conn.isOpen();
            }
        };
    }

    // Connecting -> Connected
    StateTransition getConnectingConnectedTransition() {
        return new StateTransition(ConnectionState.CONNECTED) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection connected, change state to 'connected'
                return conn != null && conn.isOpen() && conn.isConnected();
            }
        };
    }

    // Connecting -> Default
    StateTransition getConnectingDefaultTransition() {
        return new StateTransition(ConnectionState.DEFAULT) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection stopped, change state to 'not_connect'
                return conn == null || !conn.isOpen();
            }
        };
    }

    // Connected -> Expired
    StateTransition getConnectedExpiredTransition() {
        return new StateTransition(ConnectionState.EXPIRED) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                BaseConnection conn = ctx.getConnection();
                // connection still alive, but
                // long time no response, change state to 'maintain_expired'
                return conn != null && conn.isOpen() && conn.isConnected()
                        && !conn.isReceivedRecently((new Date()).getTime());
            }
        };
    }

    // Connected -> Error
    StateTransition getConnectedErrorTransition() {
        return new StateTransition(ConnectionState.ERROR) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection lost, change state to 'error'
                return conn == null || !conn.isOpen();
            }
        };
    }

    // Expired -> Maintaining
    StateTransition getExpiredMaintainingTransition() {
        return new StateTransition(ConnectionState.MAINTAINING) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                BaseConnection conn = ctx.getConnection();
                // connection still alive, and
                // sent recently, change state to 'maintaining'
                return conn != null && conn.isOpen() && conn.isConnected()
                        && conn.isSentRecently((new Date()).getTime());
            }
        };
    }

    // Expired -> Error
    StateTransition getExpiredErrorTransition() {
        return new StateTransition(ConnectionState.ERROR) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection lost, change state to 'error'
                return conn == null || !conn.isOpen();
            }
        };
    }

    // Maintaining -> Connected
    StateTransition getMaintainingConnectedTransition() {
        return new StateTransition(ConnectionState.CONNECTED) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                BaseConnection conn = ctx.getConnection();
                // connection still alive, and
                // received recently, change state to 'connected'
                return conn != null && conn.isOpen() && conn.isConnected()
                        && conn.isReceivedRecently((new Date()).getTime());
            }
        };
    }

    // Maintaining -> Expired
    StateTransition getMaintainingExpiredTransition() {
        return new StateTransition(ConnectionState.EXPIRED) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                BaseConnection conn = ctx.getConnection();
                // connection still alive, but
                // long time no sending, change state to 'maintain_expired'
                return conn != null && conn.isOpen() && conn.isConnected()
                        && !conn.isSentRecently((new Date()).getTime());
            }
        };
    }

    // Maintaining -> Error
    StateTransition getMaintainingErrorTransition() {
        return new StateTransition(ConnectionState.ERROR) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                BaseConnection conn = ctx.getConnection();
                // connection lost, or
                // long long time no response, change state to 'error
                return conn == null || !conn.isOpen()
                        || conn.isNotReceivedLongTimeAgo((new Date()).getTime());
            }
        };
    }

    // Error -> Default
    StateTransition getErrorDefaultTransition() {
        return new StateTransition(ConnectionState.DEFAULT) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection reset, change state to 'not_connect'
                return conn != null && conn.isOpen();
            }
        };
    }
}
