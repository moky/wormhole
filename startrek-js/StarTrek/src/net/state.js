;
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
//! require 'namespace.js'

(function (ns, fsm, sys) {
    'use strict';

    var Class = sys.type.Class;
    var BaseState = fsm.BaseState;

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
     * @param {String} name
     */
    var ConnectionState = function (name) {
        BaseState.call(this);
        this.__name = name;
        this.__enterTime = 0;  // timestamp (milliseconds)
    };
    Class(ConnectionState, BaseState, null, null);

    ConnectionState.DEFAULT     = 'default';
    ConnectionState.PREPARING   = 'preparing';
    ConnectionState.READY       = 'ready';
    ConnectionState.MAINTAINING = 'maintaining';
    ConnectionState.EXPIRED     = 'expired';
    ConnectionState.ERROR       = 'error';

    // Override
    ConnectionState.prototype.equals = function (other) {
        if (this === other) {
            return true;
        } else if (!other) {
            return false;
        } else if (other instanceof ConnectionState) {
            return this.__name === other.toString();
        } else {
            return this.__name === other;
        }
    };

    // Override
    ConnectionState.prototype.valueOf = function () {
        return this.__name;
    };

    // Override
    ConnectionState.prototype.toString = function () {
        return this.__name;
    };

    ConnectionState.prototype.getName = function () {
        return this.__name;
    };

    ConnectionState.prototype.getEnterTime = function () {
        return this.__enterTime;
    };

    // Override
    ConnectionState.prototype.onEnter = function (previous, machine, now) {
        this.__enterTime = now;
    };

    // Override
    ConnectionState.prototype.onExit = function (next, machine, now) {
        this.__enterTime = 0;
    };

    // Override
    ConnectionState.prototype.onPause = function (machine) {
    };

    // Override
    ConnectionState.prototype.onResume = function (machine) {
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
    var StateBuilder = function (transitionBuilder) {
        Object.call(this);
        this.builder = transitionBuilder;
    };
    Class(StateBuilder, Object, null, {
        // Connection not started yet
        getDefaultState: function () {
            var state = getNamedState(ConnectionState.DEFAULT);
            // Default -> Preparing
            state.addTransition(this.builder.getDefaultPreparingTransition());
            return state;
        },
        // Connection started, preparing to connect/bind
        getPreparingState: function () {
            var state = getNamedState(ConnectionState.PREPARING);
            // Preparing -> Ready
            state.addTransition(this.builder.getPreparingReadyTransition());
            // Preparing -> Default
            state.addTransition(this.builder.getPreparingDefaultTransition());
            return state;
        },
        // Normal state of connection
        getReadyState: function () {
            var state = getNamedState(ConnectionState.READY);
            // Ready -> Expired
            state.addTransition(this.builder.getReadyExpiredTransition());
            // Ready -> Error
            state.addTransition(this.builder.getReadyErrorTransition());
            return state;
        },
        // Long time no response, need maintaining
        getExpiredState: function () {
            var state = getNamedState(ConnectionState.EXPIRED);
            // Expired -> Maintaining
            state.addTransition(this.builder.getExpiredMaintainingTransition());
            // Expired -> Error
            state.addTransition(this.builder.getExpiredErrorTransition());
            return state;
        },
        // Heartbeat sent, waiting response
        getMaintainingState: function () {
            var state = getNamedState(ConnectionState.MAINTAINING);
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
            var state = getNamedState(ConnectionState.ERROR);
            // Error -> Default
            state.addTransition(this.builder.getErrorDefaultTransition());
            return state;
        }
    });
    var getNamedState = function (name) {
        return new ConnectionState(name);
    };

    //-------- namespace --------
    ns.net.ConnectionState = ConnectionState;
    ns.net.StateBuilder = StateBuilder;

})(StarTrek, FiniteStateMachine, MONKEY);
