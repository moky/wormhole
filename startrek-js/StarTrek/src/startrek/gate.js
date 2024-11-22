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
//! require 'net/connection.js'
//! require 'net/state.js'
//! require 'port/docker.js'
//! require 'port/gate.js'

(function (ns, sys) {
    'use strict';

    var Class                = sys.type.Class;
    var AddressPairMap       = ns.type.AddressPairMap;
    var ConnectionDelegate   = ns.net.ConnectionDelegate;
    var ConnectionStateOrder = ns.net.ConnectionStateOrder;
    var PorterStatus         = ns.port.PorterStatus;
    var Gate                 = ns.port.Gate;
    var StarPorter           = ns.StarPorter;

    var PorterPool = function () {
        AddressPairMap.call(this);
    };
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
    var StarGate = function (keeper) {
        Object.call(this);
        this.__delegate = keeper;
        this.__porterPool = this.createPorterPool();
    };
    Class(StarGate, Object, [Gate, ConnectionDelegate], null);

    // protected
    StarGate.prototype.createPorterPool = function () {
        return new PorterPool();
    };

    // protected: delegate for handling docker events
    StarGate.prototype.getDelegate = function () {
        return this.__delegate;
    };

    // Override
    StarGate.prototype.sendData = function (payload, remote, local) {
        var docker = this.getPorter(remote, local);
        if (!docker) {
            // docker not found
            return false;
        } else if (!docker.isAlive()) {
            // docker not alive
            return false;
        }
        return docker.sendData(payload);
    };

    // Override
    StarGate.prototype.sendShip = function (outgo, remote, local) {
        var docker = this.getPorter(remote, local);
        if (!docker) {
            // docker not found
            return false;
        } else if (!docker.isAlive()) {
            // docker not alive
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
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        if (!remote) {
            // remote address should not empty
            return null;
        }
        var docker;
        // try to get docker
        var old = this.getPorter(remote, local);
        if (!old && shouldCreatePorter) {
            // create & cache docker
            docker = this.createPorter(remote, local);
            var cached = this.setPorter(remote, local, docker);
            if (cached && cached !== docker) {
                cached.close();
            }
        } else {
            docker = old;
        }
        if (!old && docker instanceof StarPorter) {
            // set connection for this docker
            docker.setConnection(connection);
        }
        return docker;
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
        var cached, docker;  // Porter
        var remote, local;   // SocketAddress
        for (var i = porters.length - 1; i >= 0; --i) {
            docker = porters[i];
            if (docker.isOpen()) {
                // clear expired tasks
                docker.purge(now);
            } else {
                // remove docker when connection closed
                remote = docker.getRemoteAddress();
                local = docker.getLocalAddress();
                cached = this.removePorter(remote, local, docker);
                if (cached && cached !== docker) {
                    cached.close();
                }
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
        var docker = this.getPorter(remote, local);
        if (docker) {
            docker.heartbeat();
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
        // 1. callback when status changed
        if (s1 !== s2) {
            var notFinished = s2 !== PorterStatus.ERROR;
            var docker = this.dock(connection, notFinished);
            if (!docker) {
                // connection closed and docker removed
                return;
            }
            // callback for docker status
            var keeper = this.getDelegate();
            if (keeper) {
                keeper.onPorterStatusChanged(s1, s2, docker);
            }
        }
        // 2. heartbeat when connection expired
        var index = !current ? -1 : current.getIndex();
        if (index === ConnectionStateOrder.EXPIRED.valueOf()) {
            this.heartbeat(connection);
        }
    };

    // Override
    StarGate.prototype.onConnectionReceived = function (data, connection) {
        var docker = this.dock(connection, true);
        if (docker) {
            docker.processReceived(data);
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

    //-------- namespace --------
    ns.StarGate = StarGate;

})(StarTrek, MONKEY);
