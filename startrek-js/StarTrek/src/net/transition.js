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

    var Class          = sys.type.Class;
    var Enum           = sys.type.Enum;
    var BaseTransition = fsm.BaseTransition;
    var StateOrder     = ns.net.ConnectionStateOrder;

    /**
     *  Connection State Transition
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
     * @param {ConnectionStateOrder} order
     * @param {Function} evaluate
     */
    var StateTransition = function (order, evaluate) {
        BaseTransition.call(this, Enum.getInt(order));
        this.__evaluate = evaluate;
    };
    Class(StateTransition, BaseTransition, null, null);

    // Override
    StateTransition.prototype.evaluate = function(ctx, now) {
        return this.__evaluate.call(this, ctx, now);
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
            return new StateTransition(StateOrder.PREPARING, function (ctx, now) {
                var conn = ctx.getConnection();
                // connection started? change state to 'preparing'
                return conn && conn.isOpen();
            });
        },
        // Preparing -> Ready
        getPreparingReadyTransition: function () {
            return new StateTransition(StateOrder.READY, function (ctx, now) {
                var conn = ctx.getConnection();
                // connected or bound, change state to 'ready'
                return conn && conn.isAlive();
            });
        },
        // Preparing -> Default
        getPreparingDefaultTransition: function () {
            return new StateTransition(StateOrder.DEFAULT, function (ctx, now) {
                var conn = ctx.getConnection();
                // connection stopped, change state to 'not_connect'
                return !(conn && conn.isOpen());
            });
        },
        // Ready -> Expired
        getReadyExpiredTransition: function () {
            return new StateTransition(StateOrder.EXPIRED, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false;
                }
                // connection still alive, but
                // long time no response, change state to 'maintain_expired'
                return !conn.isReceivedRecently(now);
            });
        },
        // Ready -> Error
        getReadyErrorTransition: function () {
            return new StateTransition(StateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                // connection lost, change state to 'error'
                return !(conn && conn.isAlive());
            });
        },
        // Expired -> Maintaining
        getExpiredMaintainingTransition: function () {
            return new StateTransition(StateOrder.MAINTAINING, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false;
                }
                // connection still alive, and
                // sent recently, change state to 'maintaining'
                return conn.isSentRecently(now);
            });
        },
        // Expired -> Error
        getExpiredErrorTransition: function () {
            return new StateTransition(StateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return true;
                }
                // connection lost, or
                // long long time no response, change state to 'error'
                return conn.isNotReceivedLongTimeAgo(now);
            });
        },
        // Maintaining -> Ready
        getMaintainingReadyTransition: function () {
            return new StateTransition(StateOrder.READY, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false;
                }
                // connection still alive, and
                // received recently, change state to 'ready'
                return conn.isReceivedRecently(now);
            });
        },
        // Maintaining -> Expired
        getMaintainingExpiredTransition: function () {
            return new StateTransition(StateOrder.EXPIRED, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false;
                }
                // connection still alive, but
                // long time no sending, change state to 'maintain_expired'
                return !conn.isSentRecently(now);
            });
        },
        // Maintaining -> Error
        getMaintainingErrorTransition: function () {
            return new StateTransition(StateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return true;
                }
                // connection lost, or
                // long long time no response, change state to 'error'
                return conn.isNotReceivedLongTimeAgo(now);
            });
        },
        // Error -> Default
        getErrorDefaultTransition: function () {
            return new StateTransition(StateOrder.DEFAULT, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false;
                }
                // connection still alive, and
                // can receive data during this state
                var current = ctx.getCurrentState();
                var enter = current.getEnterTime();
                if (!enter) {
                    return true;
                }
                var last = conn.getLastReceivedTime();
                return last && enter.getTime() < last.getTime();
            });
        }
    });

    //-------- namespace --------
    ns.net.ConnectionStateTransition        = StateTransition;
    ns.net.ConnectionStateTransitionBuilder = TransitionBuilder;

})(StarTrek, FiniteStateMachine, MONKEY);
