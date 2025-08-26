'use strict';
// license: https://mit-license.org
//
//  Star Trek: Interstellar Transport
//
//                               Written in 2022 by Moky <albert.moky@gmail.com>
//
// =============================================================================
// The MIT License (MIT)
//
// Copyright (c) 2022 Albert Moky
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// =============================================================================
//

//! require <fsm.js>

    st.net.ConnectionStateOrder = Enum('ConnectionStatus', {
        DEFAULT:     0,  // Init
        PREPARING:   1,
        READY:       2,
        MAINTAINING: 3,
        EXPIRED:     4,
        ERROR:       5
    });
    var StateOrder = st.net.ConnectionStateOrder;

    /**
     *  Connection State
     *  ~~~~~~~~~~~~~~~~
     *  Defined for indicating connection state
     *
     *      DEFAULT     - 'initialized', or sent timeout
     *      PREPARING   - connecting or binding
     *      READY       - got response recently
     *      EXPIRED     - long time, needs maintaining (still connected/bound)
     *      MAINTAINING - sent 'PING', waiting for response
     *      ERROR       - long long time no response, connection lost
     *
     * @param {ConnectionStateOrder} order
     */
    st.net.ConnectionState = function (order) {
        BaseState.call(this, Enum.getInt(order));
        this.__name = order.getName();
        this.__enterTime = null;  // Date
    };
    var ConnectionState = st.net.ConnectionState;

    Class(ConnectionState, BaseState, null, {

        getName: function () {
            return this.__name;
        },

        getEnterTime: function () {
            return this.__enterTime;
        },

        // Override
        toString: function () {
            return this.__name;
        },

        // Override
        valueOf: function () {
            return this.__name;
        },

        // Override
        equals: function (other) {
            if (other instanceof ConnectionState) {
                if (other === this) {
                    // same object
                    return true;
                }
                other = other.getIndex();
            } else if (other instanceof StateOrder) {
                other = other.getValue();
            }
            return this.getIndex() === other;
        }
    });

    // Override
    ConnectionState.prototype.onEnter = function (previous, ctx, now) {
        this.__enterTime = now;
    };

    // Override
    ConnectionState.prototype.onExit = function (next, ctx, now) {
        this.__enterTime = null;
    };

    // Override
    ConnectionState.prototype.onPause = function (ctx, now) {
    };

    // Override
    ConnectionState.prototype.onResume = function (ctx, now) {
    };

    /**
     *  Connection State Delegate
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     *
     *  callback when connection state changed
     */
    ConnectionState.Delegate = fsm.Delegate;

    /**
     *  State Builder
     *  ~~~~~~~~~~~~~
     */
    st.net.ConnectionStateBuilder = function (transitionBuilder) {
        BaseObject.call(this);
        this.builder = transitionBuilder;
    };
    var StateBuilder = st.net.ConnectionStateBuilder;

    Class(StateBuilder, BaseObject, null, {

        // Connection not started yet
        getDefaultState: function () {
            var state = new ConnectionState(StateOrder.DEFAULT);
            // Default -> Preparing
            state.addTransition(this.builder.getDefaultPreparingTransition());
            return state;
        },

        // Connection started, preparing to connect/bind
        getPreparingState: function () {
            var state = new ConnectionState(StateOrder.PREPARING);
            // Preparing -> Ready
            state.addTransition(this.builder.getPreparingReadyTransition());
            // Preparing -> Default
            state.addTransition(this.builder.getPreparingDefaultTransition());
            return state;
        },

        // Normal state of connection
        getReadyState: function () {
            var state = new ConnectionState(StateOrder.READY);
            // Ready -> Expired
            state.addTransition(this.builder.getReadyExpiredTransition());
            // Ready -> Error
            state.addTransition(this.builder.getReadyErrorTransition());
            return state;
        },

        // Long time no response, need maintaining
        getExpiredState: function () {
            var state = new ConnectionState(StateOrder.EXPIRED);
            // Expired -> Maintaining
            state.addTransition(this.builder.getExpiredMaintainingTransition());
            // Expired -> Error
            state.addTransition(this.builder.getExpiredErrorTransition());
            return state;
        },

        // Heartbeat sent, waiting response
        getMaintainingState: function () {
            var state = new ConnectionState(StateOrder.MAINTAINING);
            // Maintaining -> Ready
            state.addTransition(this.builder.getMaintainingReadyTransition());
            // Maintaining -> Expired
            state.addTransition(this.builder.getMaintainingExpiredTransition());
            // Maintaining -> Error
            state.addTransition(this.builder.getMaintainingErrorTransition());
            return state;
        },

        // Connection lost
        getErrorState: function () {
            var state = new ConnectionState(StateOrder.ERROR);
            // Error -> Default
            state.addTransition(this.builder.getErrorDefaultTransition());
            return state;
        }
    });
