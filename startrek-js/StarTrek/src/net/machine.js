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
//! require 'transition.js'

/*
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
(function (ns, fsm, sys) {
    'use strict';

    var Class       = sys.type.Class;
    var Context     = fsm.Context;
    var BaseMachine = fsm.BaseMachine;

    /**
     *  Connection State Machine
     *  ~~~~~~~~~~~~~~~~~~~~~~~~
     *
     * @param {Connection|*} connection
     */
    var StateMachine = function (connection) {
        BaseMachine.call(this);
        this.__connection = connection;
        // init states
        var builder = this.createStateBuilder();
        this.addState(builder.getDefaultState());
        this.addState(builder.getPreparingState());
        this.addState(builder.getReadyState());
        this.addState(builder.getExpiredState());
        this.addState(builder.getMaintainingState());
        this.addState(builder.getErrorState());
    };
    Class(StateMachine, BaseMachine, [Context], null);

    // protected
    StateMachine.prototype.createStateBuilder = function () {
        var stb = new ns.net.ConnectionStateTransitionBuilder();
        return new ns.net.ConnectionStateBuilder(stb);
    };

    // protected
    StateMachine.prototype.getConnection = function () {
        return this.__connection;
    };

    // Override
    StateMachine.prototype.getContext = function () {
        return this;
    };

    //-------- namespace --------
    ns.net.ConnectionStateMachine = StateMachine;

})(StarTrek, FiniteStateMachine, MONKEY);
