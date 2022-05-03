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

//! require 'state.js'

(function (ns, fsm, sys) {
    'use strict';

    var Context = fsm.Context;
    var BaseMachine = fsm.BaseMachine;
    var ConnectionState = ns.net.ConnectionState;
    var StateTransition = ns.net.StateTransition;

    /**
     *  Connection State Machine
     *
     * @param {Connection} connection
     */
    var StateMachine = function (connection) {
        BaseMachine.call(this);
        this.__connection = connection;
        var builder = this.getStateBuilder();
        init_states(this, builder);
    };
    sys.Class(StateMachine, BaseMachine, [Context], null);

    // protected
    StateMachine.prototype.getStateBuilder = function () {
        return new StateBuilder(new TransitionBuilder());
    };

    // protected
    StateMachine.prototype.getConnection = function () {
        return this.__connection;
    };

    // Override
    StateMachine.prototype.getContext = function () {
        return this;
    };
    
    var add_state = function (machine, state) {
        machine.setState(state.toString(), state);
    };

    var init_states = function (machine, builder) {
        add_state(machine, builder.getDefaultState());
        add_state(machine, builder.getPreparingState());
        add_state(machine, builder.getReadyState());
        add_state(machine, builder.getExpiredState());
        add_state(machine, builder.getMaintainingState());
        add_state(machine, builder.getErrorState());
    };

    /**
     *  State Builder
     *  ~~~~~~~~~~~~~
     */
    var StateBuilder = function (transitionBuilder) {
        Object.call(this);
        this.builder = transitionBuilder;
    };
    sys.Class(StateBuilder, Object, null, {
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

    /**
     *  Transition Builder
     *  ~~~~~~~~~~~~~~~~~~
     */
    var TransitionBuilder = function () {
        Object.call(this);
    };
    sys.Class(TransitionBuilder, Object, null, {
        // Default -> Preparing
        getDefaultPreparingTransition: function () {
            return new StateTransition(ConnectionState.PREPARING, function (machine) {
                var conn = machine.getConnection();
                // connection started? change state to 'preparing'
                return conn && conn.isOpen();
            });
        },
        // Preparing -> Ready
        getPreparingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (machine) {
                var conn = machine.getConnection();
                // connected or bound, change state to 'ready'
                return conn && conn.isAlive();
            });
        },
        // Preparing -> Default
        getPreparingDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (machine) {
                var conn = machine.getConnection();
                // connection stopped, change state to 'not_connect'
                return !conn || !conn.isOpen();
            });
        },
        // Ready -> Expired
        getReadyExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, but
                // long time no response, change state to 'maintain_expired'
                return !conn.isReceivedRecently((new Date()).getTime());
            });
        },
        // Ready -> Error
        getReadyErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine) {
                var conn = machine.getConnection();
                // connection lost, change state to 'error'
                return !conn || !conn.isAlive();
            });
        },
        // Expired -> Maintaining
        getExpiredMaintainingTransition: function () {
            return new StateTransition(ConnectionState.MAINTAINING, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, and
                // sent recently, change state to 'maintaining'
                return conn.isSentRecently((new Date()).getTime());
            });
        },
        // Expired -> Error
        getExpiredErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                // connection lost, or
                // long long time no response, change state to 'error'
                return conn.isNotReceivedLongTimeAgo((new Date()).getTime());
            });
        },
        // Maintaining -> Ready
        getMaintainingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, and
                // received recently, change state to 'ready'
                return conn.isReceivedRecently((new Date()).getTime());
            });
        },
        // Maintaining -> Expired
        getMaintainingExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, but
                // long time no sending, change state to 'maintain_expired'
                return !conn.isSentRecently((new Date()).getTime());
            });
        },
        // Maintaining -> Error
        getMaintainingErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                // connection lost, or
                // long long time no response, change state to 'error'
                return conn.isNotReceivedLongTimeAgo((new Date()).getTime());
            });
        },
        // Error -> Default
        getErrorDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, and
                // can receive data during this state
                var current = machine.getCurrentState();
                var enter = current.getEnterTime();
                return 0 < enter && enter < conn.getLastReceivedTime();
            });
        }
    })

    //-------- namespace --------
    ns.net.StateMachine = StateMachine;

    ns.net.registers('StateMachine');

})(StarTrek, FiniteStateMachine, MONKEY);
