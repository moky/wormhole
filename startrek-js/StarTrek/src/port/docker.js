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

//! require 'namespace.js'

(function (ns, sys) {
    'use strict';

    var Processor = sys.skywalker.Processor;

    /**
     *  Star Worker
     *  ~~~~~~~~~~~
     *
     *  Processor for Star Ships
     */
    var Docker = function () {};
    sys.Interface(Docker, [Processor]);

    // connection.isOpen()
    Docker.prototype.isOpen = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    // connection.isAlive()
    Docker.prototype.isAlive = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    // connection.getState()
    Docker.prototype.getStatus = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    Docker.prototype.getRemoteAddress = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    // Docker.prototype.getLocalAddress = function () {
    //     ns.assert(false, 'implement me!');
    //     return null;
    // };

    /**
     *  Pack data to an outgo ship (with normal priority), and
     *  append to the waiting queue for sending out
     *
     * @param {Uint8Array} payload - data to be sent
     * @return {boolean} false on error
     */
    Docker.prototype.sendData = function (payload) {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Append outgo ship (carrying data package, with priority)
     *  to the waiting queue for sending out
     *
     * @param {Departure} ship - outgo ship carrying data package/fragment
     * @return {boolean} false on duplicated
     */
    Docker.prototype.sendShip = function (ship) {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Called when received data
     *
     * @param {Uint8Array} data - received data package
     */
    Docker.prototype.processReceived = function (data) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Send 'PING' for keeping connection alive
     */
    Docker.prototype.heartbeat = function () {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Clear all expired tasks
     */
    Docker.prototype.purge = function () {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Close connection for this docker
     */
    Docker.prototype.close = function () {
        ns.assert(false, 'implement me!');
    };

    //-------- namespace --------
    ns.port.Docker = Docker;

    ns.port.registers('Docker');

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var ConnectionState = ns.net.ConnectionState;
    var Docker = ns.port.Docker;

    /**
     *  Docker Status
     *  ~~~~~~~~~~~~~
     */
    var DockerStatus = sys.type.Enum(null, {
        ERROR:    -1,
        INIT:      0,
        PREPARING: 1,
        READY:     1
    });

    /**
     *  Convert
     *
     * @param {ConnectionState} state
     * @return {DockerStatus}
     */
    DockerStatus.getStatus = function (state) {
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

    Docker.Status = DockerStatus;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Docker = ns.port.Docker;

    /**
     *  Docker Delegate
     *  ~~~~~~~~~~~~~~~
     */
    var DockerDelegate = function () {};
    sys.Interface(DockerDelegate, null);

    /**
     *  Callback when new package received
     *
     * @param {Arrival} arrival     - income data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerReceived = function (arrival, docker) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Callback when package sent
     *
     * @param {Departure} departure - outgo data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerSent = function (departure, docker) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Callback when failed to send package
     *
     * @param {Error} error         - error message
     * @param {Departure} departure - outgo data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerFailed = function (error, departure, docker) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Callback when connection error
     *
     * @param {Error} error         - error message
     * @param {Departure} departure - outgo data package container
     * @param {Docker} docker       - connection docker
     */
    DockerDelegate.prototype.onDockerError = function (error, departure, docker) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Callback when connection status changed
     *
     * @param {Docker.Status} previous    - old status
     * @param {Docker.Status} current     - new status
     * @param {Docker} docker      - connection docker
     */
    DockerDelegate.prototype.onDockerStatusChanged = function (previous, current, docker) {
        ns.assert(false, 'implement me!');
    };

    Docker.Delegate = DockerDelegate;

})(StarTrek, MONKEY);
