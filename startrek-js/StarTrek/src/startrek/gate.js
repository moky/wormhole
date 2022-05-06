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

//! require 'type/apm.js'
//! require 'port/gate.js'

(function (ns, sys) {
    'use strict';

    var AddressPairMap = ns.type.AddressPairMap;

    var DockerPool = function () {
        AddressPairMap.call(this);
    };
    sys.Class(DockerPool, AddressPairMap, null, {
        // Override
        set: function (remote, local, value) {
            var old = this.get(remote, local);
            if (old && old !== value) {
                this.remove(remote, local, old);
            }
            AddressPairMap.prototype.set.call(this, remote, local, value);
        },
        // Override
        remove: function (remote, local, value) {
            var cached = AddressPairMap.prototype.remove.call(this, remote, local, value);
            if (cached && cached.isOpen()) {
                cached.close();
            }
            return cached;
        }
    });

    //-------- namespace --------
    ns.DockerPool = DockerPool;

    ns.registers('DockerPool');

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var ConnectionDelegate = ns.net.ConnectionDelegate;
    var ConnectionState = ns.net.ConnectionState;
    var Gate = ns.port.Gate;
    var DockerStatus = ns.port.DockerStatus;
    var DockerPool = ns.DockerPool;

    /**
     *  Base Gate
     *  ~~~~~~~~~
     *
     * @param {DockerDelegate} delegate
     */
    var StarGate = function (delegate) {
        Object.call(this);
        this.__delegate = delegate;
        this.__pool = this.createDockerPool();
    };
    sys.Class(StarGate, Object, [Gate, ConnectionDelegate], null);

    // protected
    StarGate.prototype.createDockerPool = function () {
        return new DockerPool();
    };

    // protected: delegate for handling docker events
    StarGate.prototype.getDelegate = function () {
        return this.__delegate;
    };

    // Override
    StarGate.prototype.sendData = function (payload, remote, local) {
        var docker = this.getDocker(remote, local);
        if (!docker || !docker.isOpen()) {
            return false;
        }
        return docker.sendData(payload);
    };

    // Override
    StarGate.prototype.sendShip = function (outgo, remote, local) {
        var docker = this.getDocker(remote, local);
        if (!docker || !docker.isOpen()) {
            return false;
        }
        return docker.sendShip(outgo);
    };

    //
    //  Docker
    //

    /**
     *  Create new docker for received data
     *
     * @param {Connection} connection   - current connection
     * @param {Uint8Array[]} advanceParties   - advance party
     * @return {Docker} docker
     */
    // protected
    StarGate.prototype.createDocker = function (connection, advanceParties) {
        ns.assert(false, 'implement me!');
        return null;
    };

    // protected
    StarGate.prototype.allDockers = function () {
        return this.__pool.allValues();
    };

    // protected
    StarGate.prototype.getDocker = function (remote, local) {
        return this.__pool.get(remote, local);
    };

    // protected
    StarGate.prototype.setDocker = function (remote, local, docker) {
        this.__pool.set(remote, local, docker);
    };

    // protected
    StarGate.prototype.removeDocker = function (remote, local, docker) {
        this.__pool.remove(remote, local, docker);
    };

    //
    //  Processor
    //

    // Override
    StarGate.prototype.process = function () {
        try {
            var dockers = this.allDockers();
            // 1. drive all dockers to process
            var count = this.driveDockers(dockers);
            // 2. cleanup closed dockers
            this.cleanupDockers(dockers);
            return count > 0;
        } catch (e) {
            console.error('StarGate::process()', e);
        }
    };

    // protected
    StarGate.prototype.driveDockers = function (dockers) {
        var count = 0;
        for (var index = dockers.length - 1; index >= 0; --index) {
            try {
                if (dockers[index].process()) {
                    ++count;  // it's busy
                }
            } catch (e) {
                console.error('StarGate::driveDockers()', e, dockers[index]);
            }
        }
        return count;
    };

    // protected
    StarGate.prototype.cleanupDockers = function (dockers) {
        var worker;
        for (var index = dockers.length - 1; index >= 0; --index) {
            worker = dockers[index];
            if (worker.isOpen()) {
                // clear expired tasks
                worker.purge();
            } else {
                // remove docker when connection closed
                this.removeDocker(worker.getRemoteAddress(), worker.getLocalAddress(), worker);
            }
        }
    };

    /**
     *  Send a heartbeat package('PING') to remote address
     *
     * @param {Connection} connection
     */
    // protected
    StarGate.prototype.heartbeat = function (connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        var worker = this.getDocker(remote, local);
        if (worker) {
            worker.heartbeat();
        }
    };

    //
    //  Connection Delegate
    //

    // Override
    StarGate.prototype.onConnectionStateChanged = function (previous, current, connection) {
        // 1. callback when status changed
        var delegate = this.getDelegate();
        if (delegate) {
            var s1 = DockerStatus.getStatus(previous);
            var s2 = DockerStatus.getStatus(current);
            // check status
            var changed
            if (!s1) {
                changed = !s2;
            } else if (!s2) {
                changed = true;
            } else {
                changed = !s1.equals(s2);
            }
            if (changed) {
                // callback
                var remote = connection.getRemoteAddress();
                var local = connection.getLocalAddress();
                var docker = this.getDocker(remote, local);
                // NOTICE: if the previous state is null, the docker maybe not
                //         created yet, this situation means the docker status
                //         not changed too, so no need to callback here.
                if (docker != null) {
                    delegate.onDockerStatusChanged(s1, s2, docker);
                }
            }
        }
        // 2. heartbeat when connection expired
        if (current && current.equals(ConnectionState.EXPIRED)) {
            this.heartbeat(connection);
        }
    };

    // Override
    DockerPool.prototype.onConnectionReceived = function (data, connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        // get docker by (remote, local)
        var worker = this.getDocker(remote, local);
        if (worker) {
            // docker exists, call docker.onReceived(data);
            worker.processReceived(data);
            return;
        }
        // cache advance party for this connection
        var advanceParties = this.cacheAdvanceParty(data, connection);
        // docker not exists, check the data to decide which docker should be created
        worker = this.createDocker(connection, advanceParties);
        if (worker != null) {
            // cache docker for (remote, local)
            this.setDocker(worker.getRemoteAddress(), worker.getLocalAddress(), worker);
            // process advance parties one by one
            for (var i = 0; i < advanceParties.length; ++i) {
                worker.processReceived(advanceParties[i]);
            }
            // remove advance party
            this.clearAdvanceParty(connection);
        }
    };

    // Override
    DockerPool.prototype.onConnectionSent = function (sent, data, connection) {
        // ignore event for sending success
    };

    // Override
    DockerPool.prototype.onConnectionFailed = function (error, data, connection) {
        // ignore event for sending success
    };

    // Override
    DockerPool.prototype.onConnectionError = function (error, connection) {
        // ignore event for sending success
    };

    /**
     *  Cache the advance party before decide which docker to use
     *
     * @param {Uint8Array} data
     * @param {Connection} connection
     * @return {Uint8Array[]}
     */
    // protected
    DockerPool.prototype.cacheAdvanceParty = function (data, connection) {
        ns.assert('implement me!');
        return null;
    };

    // protected
    DockerPool.prototype.clearAdvanceParty = function (connection) {
        ns.assert('implement me!');
    };

    //-------- namespace --------
    ns.DockerPool = DockerPool;

    ns.registers('DockerPool');

})(StarTrek, MONKEY);
