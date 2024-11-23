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

    var Interface = sys.type.Interface;
    var Processor = fsm.skywalker.Processor;

    /**
     *  Star Docker
     *  ~~~~~~~~~~~
     *
     *  Processor for Star Ships
     */
    var Porter = Interface(null, [Processor]);

    Porter.prototype.isOpen = function () {};     // connection.isOpen()
    Porter.prototype.isAlive = function () {};    // connection.isAlive()

    Porter.prototype.getStatus = function () {};  // connection.getState()

    Porter.prototype.getRemoteAddress = function () {};
    Porter.prototype.getLocalAddress = function () {};

    /**
     *  Pack data to an outgo ship (with normal priority), and
     *  append to the waiting queue for sending out
     *
     * @param {Uint8Array} payload - data to be sent
     * @return {boolean} false on error
     */
    Porter.prototype.sendData = function (payload) {};

    /**
     *  Append outgo ship (carrying data package, with priority)
     *  to the waiting queue for sending out
     *
     * @param {Departure} ship - outgo ship carrying data package/fragment
     * @return {boolean} false on duplicated
     */
    Porter.prototype.sendShip = function (ship) {};

    /**
     *  Called when received data
     *
     * @param {Uint8Array} data - received data package
     */
    Porter.prototype.processReceived = function (data) {};

    /**
     *  Send 'PING' for keeping connection alive
     */
    Porter.prototype.heartbeat = function () {};

    /**
     *  Clear all expired tasks
     *
     * @param {Date} now
     */
    Porter.prototype.purge = function (now) {};

    /**
     *  Close connection for this docker
     */
    Porter.prototype.close = function () {};

    //-------- namespace --------
    ns.port.Porter = Porter;

})(StarTrek, FiniteStateMachine, MONKEY);

(function (ns, sys) {
    'use strict';

    var Enum       = sys.type.Enum;
    var StateOrder = ns.net.ConnectionStateOrder;

    /**
     *  Docker Status
     *  ~~~~~~~~~~~~~
     */
    var PorterStatus = Enum('PorterStatus', {
        ERROR:    -1,
        INIT:      0,
        PREPARING: 1,
        READY:     2
    });

    /**
     *  Convert
     *
     * @param {ConnectionState|BaseState} state
     * @return {PorterStatus}
     */
    PorterStatus.getStatus = function (state) {
        if (!state) {
            return PorterStatus.ERROR;
        }
        var index = state.getIndex();
        if (StateOrder.READY.equals(index) ||
            StateOrder.EXPIRED.equals(index) ||
            StateOrder.MAINTAINING.equals(index)) {
            return PorterStatus.READY;
        } else if (StateOrder.PREPARING.equals(index)) {
            return PorterStatus.PREPARING;
        } else if (StateOrder.ERROR.equals(index)) {
            return PorterStatus.ERROR;
        } else {
            return PorterStatus.INIT;
        }
    };

    //-------- namespace --------
    ns.port.PorterStatus = PorterStatus;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;

    /**
     *  Docker Delegate
     *  ~~~~~~~~~~~~~~~
     */
    var PorterDelegate = Interface(null, null);

    /**
     *  Callback when new package received
     *
     * @param {Arrival} arrival - income data package container
     * @param {Porter} porter   - connection docker
     */
    PorterDelegate.prototype.onPorterReceived = function (arrival, porter) {};

    /**
     *  Callback when package sent
     *
     * @param {Departure} departure - outgo data package container
     * @param {Porter} porter       - connection docker
     */
    PorterDelegate.prototype.onPorterSent = function (departure, porter) {};

    /**
     *  Callback when failed to send package
     *
     * @param {Error} error         - error message
     * @param {Departure} departure - outgo data package container
     * @param {Porter} porter       - connection docker
     */
    PorterDelegate.prototype.onPorterFailed = function (error, departure, porter) {};

    /**
     *  Callback when connection error
     *
     * @param {Error} error         - error message
     * @param {Departure} departure - outgo data package container
     * @param {Porter} porter       - connection docker
     */
    PorterDelegate.prototype.onPorterError = function (error, departure, porter) {};

    /**
     *  Callback when connection status changed
     *
     * @param {PorterStatus} previous - old status
     * @param {PorterStatus} current  - new status
     * @param {Porter} porter         - connection docker
     */
    PorterDelegate.prototype.onPorterStatusChanged = function (previous, current, porter) {};

    //-------- namespace --------
    ns.port.PorterDelegate = PorterDelegate;

})(StarTrek, MONKEY);
