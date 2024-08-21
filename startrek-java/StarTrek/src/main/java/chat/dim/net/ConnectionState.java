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

import chat.dim.fsm.BaseState;
import chat.dim.fsm.State;

/**
 *  Connection State
 *  ~~~~~~~~~~~~~~~~
 *
 *  Defined for indicating connection state
 *
 *      DEFAULT     - 'initialized', or sent timeout
 *      PREPARING   - connecting or binding
 *      READY       - got response recently
 *      EXPIRED     - long time, needs maintaining (still connected/bound)
 *      MAINTAINING - sent 'PING', waiting for response
 *      ERROR       - long long time no response, connection lost
 */
public class ConnectionState extends BaseState<StateMachine, StateTransition> {

    /**
     *  Connection State Order
     *  ~~~~~~~~~~~~~~~~~~~~~~
     */
    public enum Order {
        DEFAULT,  // = 0
        PREPARING,
        READY,
        MAINTAINING,
        EXPIRED,
        ERROR
    }

    private final String name;
    private Date enterTime;

    ConnectionState(Order stateOrder) {
        super(stateOrder.ordinal());
        name = stateOrder.name();
        enterTime = null;
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof ConnectionState) {
            if (this == other) {
                return true;
            }
            ConnectionState state = (ConnectionState) other;
            return state.index == index;
        } else if (other instanceof Order) {
            return ((Order) other).ordinal() == index;
        } else {
            return false;
        }
    }
    public boolean equals(Order other) {
        return other.ordinal() == index;
    }

    @Override
    public String toString() {
        return name;
    }

    public Date getEnterTime() {
        return enterTime;
    }

    @Override
    public void onEnter(State<StateMachine, StateTransition> previous, StateMachine ctx, Date now) {
        enterTime = now;
    }

    @Override
    public void onExit(State<StateMachine, StateTransition> next, StateMachine ctx, Date now) {
        enterTime = null;
    }

    @Override
    public void onPause(StateMachine ctx, Date now) {

    }

    @Override
    public void onResume(StateMachine ctx, Date now) {

    }

    /**
     *  Connection State Delegate
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     *
     *  callback when connection state changed
     */
    public interface Delegate extends chat.dim.fsm.Delegate<StateMachine, StateTransition, ConnectionState> {

    }

    /**
     *  Connection State Builder
     *  ~~~~~~~~~~~~~~~~~~~~~~~~
     */
    static class Builder {

        private final StateTransition.Builder stb;

        Builder(StateTransition.Builder builder) {
            super();
            stb = builder;
        }

        // Connection not started yet
        ConnectionState getDefaultState() {
            ConnectionState state = new ConnectionState(ConnectionState.Order.DEFAULT);
            // Default -> Preparing
            state.addTransition(stb.getDefaultPreparingTransition());
            return state;
        }

        // Connection started, preparing to connect/bind
        ConnectionState getPreparingState() {
            ConnectionState state = new ConnectionState(ConnectionState.Order.PREPARING);
            // Preparing -> Ready
            state.addTransition(stb.getPreparingReadyTransition());
            // Preparing -> Default
            state.addTransition(stb.getPreparingDefaultTransition());
            return state;
        }

        // Normal state of connection
        ConnectionState getReadyState() {
            ConnectionState state = new ConnectionState(ConnectionState.Order.READY);
            // Ready -> Expired
            state.addTransition(stb.getReadyExpiredTransition());
            // Ready -> Error
            state.addTransition(stb.getReadyErrorTransition());
            return state;
        }

        // Long time no response, need maintaining
        ConnectionState getExpiredState() {
            ConnectionState state = new ConnectionState(ConnectionState.Order.EXPIRED);
            // Expired -> Maintaining
            state.addTransition(stb.getExpiredMaintainingTransition());
            // Expired -> Error
            state.addTransition(stb.getExpiredErrorTransition());
            return state;
        }

        // Heartbeat sent, waiting response
        ConnectionState getMaintainingState() {
            ConnectionState state = new ConnectionState(ConnectionState.Order.MAINTAINING);
            // Maintaining -> Ready
            state.addTransition(stb.getMaintainingReadyTransition());
            // Maintaining -> Expired
            state.addTransition(stb.getMaintainingExpiredTransition());
            // Maintaining -> Error
            state.addTransition(stb.getMaintainingErrorTransition());
            return state;
        }

        // Connection lost
        ConnectionState getErrorState() {
            ConnectionState state = new ConnectionState(ConnectionState.Order.ERROR);
            // Error -> Default
            state.addTransition(stb.getErrorDefaultTransition());
            return state;
        }
    }

}
