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

//! require 'state.js'
//! require 'transition.js'

(function (ns, fsm, sys) {
    'use strict';

    var Class = sys.type.Class;
    var Context = fsm.Context;
    var BaseMachine = fsm.BaseMachine;
    var ConnectionState = ns.net.ConnectionState;
    var StateBuilder = ns.net.StateBuilder;
    var TransitionBuilder = ns.net.TransitionBuilder;

    /**
     *  Connection State Machine
     *
     * @param {Connection} connection
     */
    var StateMachine = function (connection) {
        BaseMachine.call(this, ConnectionState.DEFAULT);
        this.__connection = connection;
        // init states
        var builder = this.createStateBuilder();
        add_state(this, builder.getDefaultState());
        add_state(this, builder.getPreparingState());
        add_state(this, builder.getReadyState());
        add_state(this, builder.getExpiredState());
        add_state(this, builder.getMaintainingState());
        add_state(this, builder.getErrorState());
    };
    Class(StateMachine, BaseMachine, [Context], null);

    // protected
    StateMachine.prototype.createStateBuilder = function () {
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
        machine.setState(state.getName(), state);
    };

    //-------- namespace --------
    ns.net.StateMachine = StateMachine;

})(StarTrek, FiniteStateMachine, MONKEY);
