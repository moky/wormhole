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
//! require 'port/ship.js'
//! require 'port/docker.js'
//! require 'dock.js'

    /**
     *  Base Star Docker
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     */
    st.StarPorter = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__dock = this.createDock();

        this.__conn = -1;           // Connection
        this.__delegate = null;     // PorterDelegate

        // remaining data to be sent
        this.__lastOutgo = null;    // Departure
        this.__lastFragments = [];  // Uint8Array[]
    };
    var StarPorter = st.StarPorter;

    Class(StarPorter, AddressPairObject, [Porter]);

    Implementation(StarPorter, {

        // Override
        toString: function () {
            var clazz   = this.getClassName();
            var remote  = this.getRemoteAddress();
            var local   = this.getLocalAddress();
            var conn = this.getConnection();
            return '<' + clazz + ' remote="' + remote + '" local="' + local + '">\n\t' +
                conn + '\n</' + clazz + '>';
        }
    });

    // protected: override for user-customized dock
    StarPorter.prototype.createDock = function () {
        return new Dock();
    };

    // protected
    StarPorter.prototype.getDelegate = function () {
        return this.__delegate;
    };
    // public: delegate for handling docker events
    StarPorter.prototype.setDelegate = function (keeper) {
        this.__delegate = keeper;
    };

    //
    //  Connection
    //

    StarPorter.prototype.getConnection = function () {
        var conn = this.__conn;
        return conn === -1 ? null : conn;
    };
    // protected
    StarPorter.prototype.setConnection = function (conn) {
        // 1. replace with new connection
        var old = this.__conn;
        this.__conn = conn;
        // 2. close old connection
        if (old && old !== -1 && old !== conn) {
            old.close();
        }
    };

    //
    //  Flags
    //

    // Override
    StarPorter.prototype.isOpen = function () {
        var conn = this.__conn;
        if (conn === -1) {
            // initializing
            return false;
        }
        return conn && conn.isOpen();
    };

    // Override
    StarPorter.prototype.isAlive = function () {
        var conn = this.getConnection();
        return conn && conn.isAlive();
    };

    // Override
    StarPorter.prototype.getStatus = function () {
        var conn = this.getConnection();
        if (conn) {
            return PorterStatus.getStatus(conn.getState());
        } else {
            return PorterStatus.ERROR;
        }
    };

    // Override
    StarPorter.prototype.sendShip = function (ship) {
        return this.__dock.addDeparture(ship);
    };

    // Override
    StarPorter.prototype.processReceived = function (data) {
        // 1. get income ship from received data
        var incomeShips = this.getArrivals(data);
        if (!incomeShips || incomeShips.length === 0) {
            // waiting for more data
            return;
        }
        var keeper = this.getDelegate();
        var income, ship;  // Arrival
        for (var i = 0; i < incomeShips.length; ++i) {
            ship = incomeShips[i];
            // 2. check income ship for response
            income = this.checkArrival(ship);
            if (!income) {
                // waiting for more fragment
                continue;
            }
            // 3. callback for processing income ship with completed data package
            if (keeper) {
                keeper.onPorterReceived(income, this);
            }
        }
    };

    /**
     *  Get income Ship from received data
     *
     * @param {Uint8Array} data - received data
     * @return {Arrival[]} income ships carrying data package/fragment
     */
    // protected
    StarPorter.prototype.getArrivals = function (data) {};

    /**
     *  Check income ship for responding
     *
     * @param {Arrival|Ship} income - income ship carrying data package/fragment/response
     * @return {Arrival|Ship} income ship carrying completed data package
     */
    // protected
    StarPorter.prototype.checkArrival = function (income) {};

    /**
     *  Check and remove linked departure ship with same SN (and page index for fragment)
     *
     * @param {Arrival|Ship} income - income ship with SN
     * @return {Departure|Ship} linked outgo ship
     */
    // protected
    StarPorter.prototype.checkResponse = function (income) {
        // check response for linked departure ship (same SN)
        var linked = this.__dock.checkResponse(income);
        if (!linked) {
            // linked departure task not found, or not finished yet
            return null;
        }
        // all fragments responded, task finished
        var keeper = this.getDelegate();
        if (keeper) {
            keeper.onPorterSent(linked, this);
        }
        return linked;
    };

    /**
     * Check received ship for completed package
     *
     * @param {Arrival|Ship} income - income ship carrying data package (fragment)
     * @return {Arrival|Ship} ship carrying completed data package
     */
    // protected
    StarPorter.prototype.assembleArrival = function (income) {
        return this.__dock.assembleArrival(income);
    };

    /**
     *  Get outgo Ship from waiting queue
     *
     * @param {Date} now - current time
     * @return {Departure|Ship} next new or timeout task
     */
    // protected
    StarPorter.prototype.getNextDeparture = function (now) {
        // this will be remove from the queue,
        // if needs retry, the caller should append it back
        return this.__dock.getNextDeparture(now);
    };

    // Override
    StarPorter.prototype.purge = function (now) {
        return this.__dock.purge(now);
    };

    // Override
    StarPorter.prototype.close = function () {
        this.setConnection(null);
    };

    //
    //  Processor
    //

    // Override
    StarPorter.prototype.process = function () {
        //
        //  1. get connection which is ready for sending data
        //
        var conn = this.getConnection();
        if (!conn) {
            // waiting for connection
            return false;
        } else if (!conn.isVacant()) {
            // connection is not ready for sending data
            return false;
        }
        var keeper = this.getDelegate();
        var error;  // Error
        //
        //  2. get data waiting to be sent out
        //
        var outgo = this.__lastOutgo;
        var fragments = this.__lastFragments;
        if (outgo && fragments.length > 0) {
            // got remaining fragments from last outgo task
            this.__lastOutgo = null;
            this.__lastFragments = [];
        } else {
            // get next outgo task
            var now = new Date();
            outgo = this.getNextDeparture(now);
            if (!outgo) {
                // nothing to do now, return false to let the thread have a rest
                return false;
            } else if (outgo.getStatus(now) === ShipStatus.FAILED) {
                if (keeper) {
                    // callback for mission failed
                    error = new Error('Request timeout');
                    keeper.onPorterFailed(error, outgo, this);
                }
                // task timeout, return true to process next one
                return true;
            } else {
                // get fragments from outgo task
                fragments = outgo.getFragments();
                if (fragments.length === 0) {
                    // all fragments of this task have bean sent already,
                    // return true to process next one
                    return true;
                }
            }
        }
        //
        //  3. process fragments of outgo task
        //
        var index = 0;
        var sent = 0;
        try {
            var fra;
            for (var i = 0; i < fragments.length; ++i) {
                fra = fragments[i];
                sent = conn.sendData(fra);
                if (sent < fra.length) {
                    // buffer overflow?
                    break;
                } else {
                    index += 1;
                    sent = 0;  // clear counter
                }
            }
            if (index < fragments.length) {
                // task failed
                error = new Error('only ' + index + '/' + fragments.length + ' fragments sent.');
            } else {
                // task done
                if (outgo.isImportant()) {
                    // this task needs response,
                    // so we cannot call 'onPorterSent()' immediately
                    // until the remote responded
                } else if (keeper) {
                    keeper.onPorterSent(outgo, this);
                }
                return true;
            }
        } catch (e) {
            // socket error, callback
            error = e;
        }
        //
        //  4. remove sent fragments
        //
        for (; index > 0; --index) {
            fragments.shift();
        }
        // remove partially sent data of next fragment
        if (sent > 0) {
            var last = fragments.shift();
            var part = last.subarray(sent);
            fragments.unshift(part);
        }
        //
        //  5. store remaining data
        //
        this.__lastOutgo = outgo;
        this.__lastFragments = fragments;
        //
        //  6. callback for error
        //
        if (keeper) {
            // keeper.onPorterFailed(error, outgo, this);
            keeper.onPorterError(error, outgo, this);
        }
        return false;
    };
