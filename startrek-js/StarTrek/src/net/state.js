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

/**
 *    Finite States:
 *
 *             //===============\\          (Start)          //=============\\
 *             ||               || ------------------------> ||             ||
 *             ||    Default    ||                           ||  Preparing  ||
 *             ||               || <------------------------ ||             ||
 *             \\===============//         (Timeout)         \\=============//
 *                                                               |       |
 *             //===============\\                               |       |
 *             ||               || <-----------------------------+       |
 *             ||     Error     ||          (Error)                 (Connected
 *             ||               || <-----------------------------+   or bound)
 *             \\===============//                               |       |
 *                 A       A                                     |       |
 *                 |       |            //===========\\          |       |
 *                 (Error) +----------- ||           ||          |       |
 *                 |                    ||  Expired  || <--------+       |
 *                 |       +----------> ||           ||          |       |
 *                 |       |            \\===========//          |       |
 *                 |       (Timeout)           |         (Timeout)       |
 *                 |       |                   |                 |       V
 *             //===============\\     (Sent)  |             //=============\\
 *             ||               || <-----------+             ||             ||
 *             ||  Maintaining  ||                           ||    Ready    ||
 *             ||               || ------------------------> ||             ||
 *             \\===============//       (Received)          \\=============//
 */

//! require 'namespace.js'

(function (ns, fsm, sys) {
    'use strict';

    var Stringer = sys.type.Stringer;
    var BaseState = fsm.BaseState;

    /**
     *  Connection State
     *  ~~~~~~~~~~~~~~~~
     *
     * @param {String} name
     */
    var ConnectionState = function (name) {
        BaseState.call(this);
        this.__name = name;
        this.__enterTime = 0;  // timestamp (milliseconds)
    };
    sys.Class(ConnectionState, BaseState, null, null);

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
        } else if (other instanceof ConnectionState) {
            return this.__name === other.toString();
        } else if (ns.Interface.conforms(other, Stringer)) {
            return this.__name === other.toString();
        } else {
            return this.__name === other;
        }
    };

    ConnectionState.prototype.toString = function () {
        return this.__name;
    };

    ConnectionState.prototype.getEnterTime = function () {
        return this.__enterTime;
    };

    // Override
    ConnectionState.prototype.onEnter = function (machine) {
        this.__enterTime = (new Date()).getTime();
    };

    // Override
    ConnectionState.prototype.onExit = function (machine) {
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

    //-------- namespace --------
    ns.net.ConnectionState = ConnectionState;

    ns.net.registers('ConnectionState');

})(StarTrek, FiniteStateMachine, MONKEY);

(function (ns, fsm, sys) {
    'use strict';

    var BaseTransition = fsm.BaseTransition;

    var StateTransition = function (targetStateName, evaluate) {
        BaseTransition.call(this, targetStateName);
        this.__evaluate = evaluate;
    };
    sys.Class(StateTransition, BaseTransition, null, null);

    // Override
    StateTransition.prototype.evaluate = function(machine) {
        return this.__evaluate.call(this, machine);
    };

    //-------- namespace --------
    ns.net.StateTransition = StateTransition;

    ns.net.registers('StateTransition');

})(StarTrek, FiniteStateMachine, MONKEY);
