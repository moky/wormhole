'use strict';
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
//! require 'net/connection.js'
//! require 'net/state.js'
//! require 'port/docker.js'
//! require 'port/gate.js'

    st.PorterPool = function () {
        AddressPairMap.call(this);
    };
    var PorterPool = st.PorterPool;

    Class(PorterPool, AddressPairMap, null, {

        // Override
        set: function (remote, local, value) {
            // remove cached item
            var cached = AddressPairMap.prototype.remove.call(this, remote, local, value);
            // if (cached && cached !== value) {
            //     cached.close();
            // }
            AddressPairMap.prototype.set.call(this, remote, local, value);
            return cached;
        }

        // // Override
        // remove: function (remote, local, value) {
        //     var cached = AddressPairMap.prototype.remove.call(this, remote, local, value);
        //     if (cached && cached !== value) {
        //         cached.close();
        //     }
        //     if (value) {
        //         value.close();
        //     }
        //     return cached;
        // }
    });


    /**
     *  Base Star Gate
     *  ~~~~~~~~~~~~~~
     *
     * @param {PorterDelegate} keeper
     */
    st.StarGate = function (keeper) {
        BaseObject.call(this);
        this.__delegate = keeper;
        this.__porterPool = this.createPorterPool();
    };
    var StarGate = st.StarGate;

    Class(StarGate, BaseObject, [Gate, ConnectionDelegate], null);

    // protected
    StarGate.prototype.createPorterPool = function () {
        return new PorterPool();
    };

    // protected: delegate for handling porter events
    StarGate.prototype.getDelegate = function () {
        return this.__delegate;
    };

    // Override
    StarGate.prototype.sendData = function (payload, remote, local) {
        var worker = this.getPorter(remote, local);
        if (!worker) {
            // porter not found
            return false;
        } else if (!worker.isAlive()) {
            // porter not alive
            return false;
        }
        return worker.sendData(payload);
    };

    // Override
    StarGate.prototype.sendShip = function (outgo, remote, local) {
        var worker = this.getPorter(remote, local);
        if (!worker) {
            // porter not found
            return false;
        } else if (!worker.isAlive()) {
            // porter not alive
            return false;
        }
        return worker.sendShip(outgo);
    };

    //
    //  Docker
    //

    /**
     *  Create new porter for received data
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     * @return {Porter} docker
     */
    // protected
    StarGate.prototype.createPorter = function (remote, local) {};

    // protected
    StarGate.prototype.allPorters = function () {
        return this.__porterPool.items();
    };

    // protected
    StarGate.prototype.getPorter = function (remote, local) {
        return this.__porterPool.get(remote, local);
    };

    // protected
    StarGate.prototype.setPorter = function (remote, local, porter) {
        return this.__porterPool.set(remote, local, porter);
    };

    // protected
    StarGate.prototype.removePorter = function (remote, local, porter) {
        return this.__porterPool.remove(remote, local, porter);
    };

    // protected
    StarGate.prototype.dock = function (connection, shouldCreatePorter) {
        //
        //  0. pre-checking
        //
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        if (!remote) {
            // remote address should not empty
            return null;
        }
        var worker, cached;
        //
        //  1. try to get porter
        //
        worker = this.getPorter(remote, local);
        if (worker) {
            // found
            return worker;
        } else if (!shouldCreatePorter) {
            // no need to create new porter
            return null;
        }
        //
        //  2. create new porter
        //
        worker = this.createPorter(remote, local);
        cached = this.setPorter(remote, local, worker);
        if (cached && cached !== worker) {
            cached.close();
        }
        //
        //  3. set connection for this porter
        //
        if (worker instanceof StarPorter) {
            // set connection for this porter
            worker.setConnection(connection);
        }
        return worker;
    };

    //
    //  Processor
    //

    // Override
    StarGate.prototype.process = function () {
        var dockers = this.allPorters();
        // 1. drive all dockers to process
        var count = this.drivePorters(dockers);
        // 2. cleanup closed dockers
        this.cleanupPorters(dockers);
        return count > 0;
    };

    // protected
    StarGate.prototype.drivePorters = function (porters) {
        var count = 0;
        for (var i = porters.length - 1; i >= 0; --i) {
            if (porters[i].process()) {
                ++count;  // it's busy
            }
        }
        return count;
    };

    // protected
    StarGate.prototype.cleanupPorters = function (porters) {
        var now = new Date();
        var cached, worker;  // Porter
        var remote, local;   // SocketAddress
        for (var i = porters.length - 1; i >= 0; --i) {
            worker = porters[i];
            if (worker.isOpen()) {
                // clear expired tasks
                worker.purge(now);
                continue;
            }
            // remove porter when connection closed
            remote = worker.getRemoteAddress();
            local = worker.getLocalAddress();
            cached = this.removePorter(remote, local, worker);
            if (cached && cached !== worker) {
                cached.close();
            }
        }
    };

    /**
     *  Send a heartbeat package('PING') to remote address
     *
     * @param {st.net.Connection} connection
     */
    // protected
    StarGate.prototype.heartbeat = function (connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        var worker = this.getPorter(remote, local);
        if (worker) {
            worker.heartbeat();
        }
    };

    //
    //  Connection Delegate
    //

    // Override
    StarGate.prototype.onConnectionStateChanged = function (previous, current, connection) {
        // convert status
        var s1 = PorterStatus.getStatus(previous);
        var s2 = PorterStatus.getStatus(current);
        //
        //  1. callback when status changed
        //
        if (s1 !== s2) {
            var notFinished = s2 !== PorterStatus.ERROR;
            var worker = this.dock(connection, notFinished);
            if (!worker) {
                // connection closed and porter removed
                return;
            }
            // callback for porter status
            var keeper = this.getDelegate();
            if (keeper) {
                keeper.onPorterStatusChanged(s1, s2, worker);
            }
        }
        //
        //  2. heartbeat when connection expired
        //
        var index = !current ? -1 : current.getIndex();
        if (StateOrder.EXPIRED.equals(index)) {
            this.heartbeat(connection);
        }
    };

    // Override
    StarGate.prototype.onConnectionReceived = function (data, connection) {
        var worker = this.dock(connection, true);
        if (worker) {
            worker.processReceived(data);
        }
    };

    // Override
    StarGate.prototype.onConnectionSent = function (sent, data, connection) {
        // ignore event for sending success
    };

    // Override
    StarGate.prototype.onConnectionFailed = function (error, data, connection) {
        // ignore event for sending success
    };

    // Override
    StarGate.prototype.onConnectionError = function (error, connection) {
        // ignore event for sending success
    };
