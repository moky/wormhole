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

    public static final String DEFAULT     = "default";
    public static final String PREPARING   = "preparing";
    public static final String READY       = "ready";
    public static final String MAINTAINING = "maintaining";
    public static final String EXPIRED     = "expired";
    public static final String ERROR       = "error";

    public final String name;
    private long enterTime;

    ConnectionState(String stateName) {
        super();
        name = stateName;
        enterTime = 0;
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof ConnectionState) {
            if (this == other) {
                return true;
            }
            ConnectionState state = (ConnectionState) other;
            return name.equals(state.name);
        } else if (other instanceof String) {
            return name.equals(other);
        } else {
            return false;
        }
    }
    public boolean equals(String other) {
        return name.equals(other);
    }

    @Override
    public String toString() {
        return name;
    }

    public long getEnterTime() {
        return enterTime;
    }

    @Override
    public void onEnter(State<StateMachine, StateTransition> previous, StateMachine ctx) {
        enterTime = System.currentTimeMillis();
    }

    @Override
    public void onExit(State<StateMachine, StateTransition> next, StateMachine ctx) {
        enterTime = 0;
    }

    @Override
    public void onPause(StateMachine ctx) {

    }

    @Override
    public void onResume(StateMachine ctx) {

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
     *  State Builder
     *  ~~~~~~~~~~~~~
     */
    static class Builder {

        private final StateTransition.Builder stb;

        Builder(StateTransition.Builder builder) {
            super();
            stb = builder;
        }

        // Connection not started yet
        ConnectionState getDefaultState() {
            ConnectionState state = new ConnectionState(ConnectionState.DEFAULT);
            // Default -> Preparing
            state.addTransition(stb.getDefaultPreparingTransition());
            return state;
        }

        // Connection started, preparing to connect/bind
        ConnectionState getPreparingState() {
            ConnectionState state = new ConnectionState(ConnectionState.PREPARING);
            // Preparing -> Ready
            state.addTransition(stb.getPreparingReadyTransition());
            // Preparing -> Default
            state.addTransition(stb.getPreparingDefaultTransition());
            return state;
        }

        // Normal state of connection
        ConnectionState getReadyState() {
            ConnectionState state = new ConnectionState(ConnectionState.READY);
            // Ready -> Expired
            state.addTransition(stb.getReadyExpiredTransition());
            // Ready -> Error
            state.addTransition(stb.getReadyErrorTransition());
            return state;
        }

        // Long time no response, need maintaining
        ConnectionState getExpiredState() {
            ConnectionState state = new ConnectionState(ConnectionState.EXPIRED);
            // Expired -> Maintaining
            state.addTransition(stb.getExpiredMaintainingTransition());
            // Expired -> Error
            state.addTransition(stb.getExpiredErrorTransition());
            return state;
        }

        // Heartbeat sent, waiting response
        ConnectionState getMaintainingState() {
            ConnectionState state = new ConnectionState(ConnectionState.MAINTAINING);
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
            ConnectionState state = new ConnectionState(ConnectionState.ERROR);
            // Error -> Default
            state.addTransition(stb.getErrorDefaultTransition());
            return state;
        }
    }
}
