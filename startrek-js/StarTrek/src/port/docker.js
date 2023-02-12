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
     *  Star Worker
     *  ~~~~~~~~~~~
     *
     *  Processor for Star Ships
     */
    var Docker = Interface(null, [Processor]);

    // connection.isOpen()
    Docker.prototype.isOpen = function () {
        throw new Error('NotImplemented');
    };

    // connection.isAlive()
    Docker.prototype.isAlive = function () {
        throw new Error('NotImplemented');
    };

    // connection.getState()
    Docker.prototype.getStatus = function () {
        throw new Error('NotImplemented');
    };

    Docker.prototype.getRemoteAddress = function () {
        throw new Error('NotImplemented');
    };

    Docker.prototype.getLocalAddress = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Pack data to an outgo ship (with normal priority), and
     *  append to the waiting queue for sending out
     *
     * @param {Uint8Array} payload - data to be sent
     * @return {boolean} false on error
     */
    Docker.prototype.sendData = function (payload) {
        throw new Error('NotImplemented');
    };

    /**
     *  Append outgo ship (carrying data package, with priority)
     *  to the waiting queue for sending out
     *
     * @param {Departure} ship - outgo ship carrying data package/fragment
     * @return {boolean} false on duplicated
     */
    Docker.prototype.sendShip = function (ship) {
        throw new Error('NotImplemented');
    };

    /**
     *  Called when received data
     *
     * @param {Uint8Array} data - received data package
     */
    Docker.prototype.processReceived = function (data) {
        throw new Error('NotImplemented');
    };

    /**
     *  Send 'PING' for keeping connection alive
     */
    Docker.prototype.heartbeat = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Clear all expired tasks
     */
    Docker.prototype.purge = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Close connection for this docker
     */
    Docker.prototype.close = function () {
        throw new Error('NotImplemented');
    };

    //-------- namespace --------
    ns.port.Docker = Docker;

})(StarTrek, FiniteStateMachine, MONKEY);

(function (ns, sys) {
    'use strict';

    var Enum = sys.type.Enum;

    /**
     *  Docker Status
     *  ~~~~~~~~~~~~~
     */
    var DockerStatus = Enum(null, {
        ERROR:    -1,
        INIT:      0,
        PREPARING: 1,
        READY:     2
    });

    /**
     *  Convert
     *
     * @param {ConnectionState} state
     * @return {DockerStatus}
     */
    DockerStatus.getStatus = function (state) {
        var ConnectionState = ns.net.ConnectionState;
        if (!state) {
            return DockerStatus.ERROR;
        } else if (state.equals(ConnectionState.READY)
            || state.equals(ConnectionState.EXPIRED)
            || state.equals(ConnectionState.MAINTAINING)) {
            return DockerStatus.READY;
        } else if (state.equals(ConnectionState.PREPARING)) {
            return DockerStatus.PREPARING;
        } else if (state.equals(ConnectionState.ERROR)) {
            return DockerStatus.ERROR;
        } else {
            return DockerStatus.INIT;
        }
    };

    //-------- namespace --------
    ns.port.DockerStatus = DockerStatus;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;

    /**
     *  Docker Delegate
     *  ~~~~~~~~~~~~~~~
     */
    var DockerDelegate = Interface(null, null);

    /**
     *  Callback when new package received
     *
     * @param {Arrival} arrival     - income data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerReceived = function (arrival, docker) {
        throw new Error('NotImplemented');
    };

    /**
     *  Callback when package sent
     *
     * @param {Departure} departure - outgo data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerSent = function (departure, docker) {
        throw new Error('NotImplemented');
    };

    /**
     *  Callback when failed to send package
     *
     * @param {Error} error         - error message
     * @param {Departure} departure - outgo data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerFailed = function (error, departure, docker) {
        throw new Error('NotImplemented');
    };

    /**
     *  Callback when connection error
     *
     * @param {Error} error         - error message
     * @param {Departure} departure - outgo data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerError = function (error, departure, docker) {
        throw new Error('NotImplemented');
    };

    /**
     *  Callback when connection status changed
     *
     * @param {DockerStatus} previous    - old status
     * @param {DockerStatus} current     - new status
     * @param {Docker} docker      - connection docker
     */
    DockerDelegate.prototype.onDockerStatusChanged = function (previous, current, docker) {
        throw new Error('NotImplemented');
    };

    //-------- namespace --------
    ns.port.DockerDelegate = DockerDelegate;

})(StarTrek, MONKEY);
