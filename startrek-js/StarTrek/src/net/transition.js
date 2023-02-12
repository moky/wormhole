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

    var Class = sys.type.Class;
    var BaseTransition = fsm.BaseTransition;
    var ConnectionState = ns.net.ConnectionState;

    var StateTransition = function (targetStateName, evaluate) {
        BaseTransition.call(this, targetStateName);
        this.__evaluate = evaluate;
    };
    Class(StateTransition, BaseTransition, null, null);

    // Override
    StateTransition.prototype.evaluate = function(machine, now) {
        return this.__evaluate.call(this, machine, now);
    };

    /**
     *  Transition Builder
     *  ~~~~~~~~~~~~~~~~~~
     */
    var TransitionBuilder = function () {
        Object.call(this);
    };
    Class(TransitionBuilder, Object, null, {
        // Default -> Preparing
        getDefaultPreparingTransition: function () {
            return new StateTransition(ConnectionState.PREPARING, function (machine, now) {
                var conn = machine.getConnection();
                // connection started? change state to 'preparing'
                return conn && conn.isOpen();
            });
        },
        // Preparing -> Ready
        getPreparingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (machine, now) {
                var conn = machine.getConnection();
                // connected or bound, change state to 'ready'
                return conn && conn.isAlive();
            });
        },
        // Preparing -> Default
        getPreparingDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (machine, now) {
                var conn = machine.getConnection();
                // connection stopped, change state to 'not_connect'
                return !conn || !conn.isOpen();
            });
        },
        // Ready -> Expired
        getReadyExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (machine, now) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, but
                // long time no response, change state to 'maintain_expired'
                return !conn.isReceivedRecently(now);
            });
        },
        // Ready -> Error
        getReadyErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine, now) {
                var conn = machine.getConnection();
                // connection lost, change state to 'error'
                return !conn || !conn.isAlive();
            });
        },
        // Expired -> Maintaining
        getExpiredMaintainingTransition: function () {
            return new StateTransition(ConnectionState.MAINTAINING, function (machine, now) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, and
                // sent recently, change state to 'maintaining'
                return conn.isSentRecently(now);
            });
        },
        // Expired -> Error
        getExpiredErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine, now) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                // connection lost, or
                // long long time no response, change state to 'error'
                return conn.isNotReceivedLongTimeAgo(now);
            });
        },
        // Maintaining -> Ready
        getMaintainingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (machine, now) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, and
                // received recently, change state to 'ready'
                return conn.isReceivedRecently(now);
            });
        },
        // Maintaining -> Expired
        getMaintainingExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (machine, now) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                // connection still alive, but
                // long time no sending, change state to 'maintain_expired'
                return !conn.isSentRecently(now);
            });
        },
        // Maintaining -> Error
        getMaintainingErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine, now) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                // connection lost, or
                // long long time no response, change state to 'error'
                return conn.isNotReceivedLongTimeAgo(now);
            });
        },
        // Error -> Default
        getErrorDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (machine, now) {
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
    ns.net.StateTransition = StateTransition;
    ns.net.TransitionBuilder = TransitionBuilder;

})(StarTrek, FiniteStateMachine, MONKEY);
