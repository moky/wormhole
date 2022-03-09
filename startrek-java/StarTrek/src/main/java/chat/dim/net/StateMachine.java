/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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

abstract class StateTransition extends BaseTransition<StateMachine> {

    protected StateTransition(String target) {
        super(target);
    }
}

public class StateMachine extends BaseMachine<StateMachine, StateTransition, ConnectionState>
        implements Context {

    private final WeakReference<Connection> connectionRef;

    public StateMachine(Connection connection) {
        super(ConnectionState.DEFAULT);

        connectionRef = new WeakReference<>(connection);

        // init states
        StateBuilder builder = getStateBuilder();
        addState(builder.getDefaultState());
        addState(builder.getPreparingState());
        addState(builder.getReadyState());
        addState(builder.getExpiredState());
        addState(builder.getMaintainingState());
        addState(builder.getErrorState());
    }

    protected StateBuilder getStateBuilder() {
        return new StateBuilder(new TransitionBuilder());
    }

    private void addState(ConnectionState state) {
        setState(state.name, state);
    }

    @Override
    protected StateMachine getContext() {
        return this;
    }

    Connection getConnection() {
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
        // Default -> Preparing
        state.addTransition(builder.getDefaultPreparingTransition());
        return state;
    }

    // Connection started, preparing to connect/bind
    ConnectionState getPreparingState() {
        ConnectionState state = getNamedState(ConnectionState.PREPARING);
        // Preparing -> Ready
        state.addTransition(builder.getPreparingReadyTransition());
        // Preparing -> Default
        state.addTransition(builder.getPreparingDefaultTransition());
        return state;
    }

    // Normal state of connection
    ConnectionState getReadyState() {
        ConnectionState state = getNamedState(ConnectionState.READY);
        // Ready -> Expired
        state.addTransition(builder.getReadyExpiredTransition());
        // Ready -> Error
        state.addTransition(builder.getReadyErrorTransition());
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
        // Maintaining -> Ready
        state.addTransition(builder.getMaintainingReadyTransition());
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

    // Default -> Preparing
    StateTransition getDefaultPreparingTransition() {
        return new StateTransition(ConnectionState.PREPARING) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection started? change state to 'preparing'
                return conn != null && conn.isOpen();
            }
        };
    }

    // Preparing -> Ready
    StateTransition getPreparingReadyTransition() {
        return new StateTransition(ConnectionState.READY) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connected or bound, change state to 'ready'
                return conn != null && conn.isAlive();
            }
        };
    }

    // Preparing -> Default
    StateTransition getPreparingDefaultTransition() {
        return new StateTransition(ConnectionState.DEFAULT) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection stopped, change state to 'not_connect'
                return conn == null || !conn.isOpen();
            }
        };
    }

    // Ready -> Expired
    StateTransition getReadyExpiredTransition() {
        return new StateTransition(ConnectionState.EXPIRED) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                if (conn == null || !conn.isAlive()) {
                    return false;
                }
                TimedConnection timed = (TimedConnection) conn;
                // connection still alive, but
                // long time no response, change state to 'maintain_expired'
                return !timed.isReceivedRecently((new Date()).getTime());
            }
        };
    }

    // Ready -> Error
    StateTransition getReadyErrorTransition() {
        return new StateTransition(ConnectionState.ERROR) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                // connection lost, change state to 'error'
                return conn == null || !conn.isAlive();
            }
        };
    }

    // Expired -> Maintaining
    StateTransition getExpiredMaintainingTransition() {
        return new StateTransition(ConnectionState.MAINTAINING) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                if (conn == null || !conn.isAlive()) {
                    return false;
                }
                TimedConnection timed = (TimedConnection) conn;
                // connection still alive, and
                // sent recently, change state to 'maintaining'
                return timed.isSentRecently((new Date()).getTime());
            }
        };
    }

    // Expired -> Error
    StateTransition getExpiredErrorTransition() {
        return new StateTransition(ConnectionState.ERROR) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                if (conn == null || !conn.isAlive()) {
                    return true;
                }
                TimedConnection timed = (TimedConnection) conn;
                // connection lost, or
                // long long time no response, change state to 'error'
                return timed.isNotReceivedLongTimeAgo((new Date()).getTime());
            }
        };
    }

    // Maintaining -> Ready
    StateTransition getMaintainingReadyTransition() {
        return new StateTransition(ConnectionState.READY) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                if (conn == null || !conn.isAlive()) {
                    return false;
                }
                TimedConnection timed = (TimedConnection) conn;
                // connection still alive, and
                // received recently, change state to 'ready'
                return timed.isReceivedRecently((new Date()).getTime());
            }
        };
    }

    // Maintaining -> Expired
    StateTransition getMaintainingExpiredTransition() {
        return new StateTransition(ConnectionState.EXPIRED) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                if (conn == null || !conn.isAlive()) {
                    return false;
                }
                TimedConnection timed = (TimedConnection) conn;
                // connection still alive, but
                // long time no sending, change state to 'maintain_expired'
                return !timed.isSentRecently((new Date()).getTime());
            }
        };
    }

    // Maintaining -> Error
    StateTransition getMaintainingErrorTransition() {
        return new StateTransition(ConnectionState.ERROR) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                if (conn == null || !conn.isAlive()) {
                    return true;
                }
                TimedConnection timed = (TimedConnection) conn;
                // connection lost, or
                // long long time no response, change state to 'error'
                return timed.isNotReceivedLongTimeAgo((new Date()).getTime());
            }
        };
    }

    // Error -> Default
    StateTransition getErrorDefaultTransition() {
        return new StateTransition(ConnectionState.DEFAULT) {
            @Override
            public boolean evaluate(StateMachine ctx) {
                Connection conn = ctx.getConnection();
                if (conn == null || !conn.isAlive()) {
                    return false;
                }
                TimedConnection timed = (TimedConnection) conn;
                // connection still alive, and
                // can receive data during this state
                ConnectionState current = ctx.getCurrentState();
                long enter = current.getEnterTime();
                return 0 < enter && enter < timed.getLastReceivedTime();
            }
        };
    }
}
