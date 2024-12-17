/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
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

import java.util.Date;

import chat.dim.fsm.BaseTransition;

/**
 *  Connection State Transition
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public abstract class ConnectionStateTransition extends BaseTransition<ConnectionStateMachine> {

    protected ConnectionStateTransition(ConnectionState.Order order) {
        super(order.ordinal());
    }

    /**
     *  Connection State Transition Builder
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    static class Builder {

        // Default -> Preparing
        ConnectionStateTransition getDefaultPreparingTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.PREPARING) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    // connection started? change state to 'preparing'
                    return conn != null && conn.isOpen();
                }
            };
        }

        // Preparing -> Ready
        ConnectionStateTransition getPreparingReadyTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.READY) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    // connected or bound, change state to 'ready'
                    return conn != null && conn.isAlive();
                }
            };
        }

        // Preparing -> Default
        ConnectionStateTransition getPreparingDefaultTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.DEFAULT) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    // connection stopped, change state to 'not_connect'
                    return conn == null || !conn.isOpen();
                }
            };
        }

        // Ready -> Expired
        ConnectionStateTransition getReadyExpiredTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.EXPIRED) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    if (conn == null || !conn.isAlive()) {
                        return false;
                    }
                    TimedConnection timed = (TimedConnection) conn;
                    // connection still alive, but
                    // long time no response, change state to 'maintain_expired'
                    return !timed.isReceivedRecently(now);
                }
            };
        }

        // Ready -> Error
        ConnectionStateTransition getReadyErrorTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.ERROR) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    // connection lost, change state to 'error'
                    return conn == null || !conn.isAlive();
                }
            };
        }

        // Expired -> Maintaining
        ConnectionStateTransition getExpiredMaintainingTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.MAINTAINING) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    if (conn == null || !conn.isAlive()) {
                        return false;
                    }
                    TimedConnection timed = (TimedConnection) conn;
                    // connection still alive, and
                    // sent recently, change state to 'maintaining'
                    return timed.isSentRecently(now);
                }
            };
        }

        // Expired -> Error
        ConnectionStateTransition getExpiredErrorTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.ERROR) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    if (conn == null || !conn.isAlive()) {
                        return true;
                    }
                    TimedConnection timed = (TimedConnection) conn;
                    // connection lost, or
                    // long long time no response, change state to 'error'
                    return timed.isNotReceivedLongTimeAgo(now);
                }
            };
        }

        // Maintaining -> Ready
        ConnectionStateTransition getMaintainingReadyTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.READY) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    if (conn == null || !conn.isAlive()) {
                        return false;
                    }
                    TimedConnection timed = (TimedConnection) conn;
                    // connection still alive, and
                    // received recently, change state to 'ready'
                    return timed.isReceivedRecently(now);
                }
            };
        }

        // Maintaining -> Expired
        ConnectionStateTransition getMaintainingExpiredTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.EXPIRED) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    if (conn == null || !conn.isAlive()) {
                        return false;
                    }
                    TimedConnection timed = (TimedConnection) conn;
                    // connection still alive, but
                    // long time no sending, change state to 'maintain_expired'
                    return !timed.isSentRecently(now);
                }
            };
        }

        // Maintaining -> Error
        ConnectionStateTransition getMaintainingErrorTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.ERROR) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    if (conn == null || !conn.isAlive()) {
                        return true;
                    }
                    TimedConnection timed = (TimedConnection) conn;
                    // connection lost, or
                    // long long time no response, change state to 'error'
                    return timed.isNotReceivedLongTimeAgo(now);
                }
            };
        }

        // Error -> Default
        ConnectionStateTransition getErrorDefaultTransition() {
            return new ConnectionStateTransition(ConnectionState.Order.DEFAULT) {
                @Override
                public boolean evaluate(ConnectionStateMachine ctx, Date now) {
                    Connection conn = ctx.getConnection();
                    if (conn == null || !conn.isAlive()) {
                        return false;
                    }
                    TimedConnection timed = (TimedConnection) conn;
                    // connection still alive, and
                    // can receive data during this state
                    ConnectionState current = ctx.getCurrentState();
                    Date enter = current.getEnterTime();
                    Date last = timed.getLastReceivedTime();
                    if (enter == null) {
                        assert false : "should not happen";
                        return true;
                    }
                    return last != null && enter.before(last);
                    //return 0 < enter && enter < timed.getLastReceivedTime();
                }
            };
        }
    }

}
