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
//! require 'net/hub.js'

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var AddressPairMap = ns.type.AddressPairMap;
    var Hub = ns.net.Hub;

    var ConnectionPool = function () {
        AddressPairMap.call(this);
    };
    Class(ConnectionPool, AddressPairMap, null, {
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

    /**
     *  Base Hub
     *  ~~~~~~~~
     *
     * @param {ConnectionDelegate} delegate
     */
    var BaseHub = function (delegate) {
        Object.call(this);
        this.__delegate = delegate;
        this.__connPool = this.createConnectionPool();
        // last time drove connections
        this.__last = (new Date()).getTime();
    };
    Class(BaseHub, Object, [Hub], null);

    // protected
    BaseHub.prototype.createConnectionPool = function () {
        return new ConnectionPool();
    };

    // protected: delegate for handling connection events
    BaseHub.prototype.getDelegate = function () {
        return this.__delegate;
    };

    /*  Maximum Segment Size
     *  ~~~~~~~~~~~~~~~~~~~~
     *  Buffer size for receiving package
     *
     *  MTU        : 1500 bytes (excludes 14 bytes ethernet header & 4 bytes FCS)
     *  IP header  :   20 bytes
     *  TCP header :   20 bytes
     *  UDP header :    8 bytes
     */
    BaseHub.MSS = 1472;  // 1500 - 20 - 8

    //
    //  Channel
    //

    /**
     *  Get all channels
     *
     * @return {Channel[]} copy of channels
     */
    // protected
    BaseHub.prototype.allChannels = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Remove socket channel
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     * @param {Channel} channel
     */
    // protected
    BaseHub.prototype.removeChannel = function (remote, local, channel) {
        throw new Error('NotImplemented');
    };

    //
    //  Connections
    //

    /**
     *  Create connection with socket channel & addresses
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     * @param {Channel} channel
     * @return {Connection} null on channel not exists
     */
    // protected
    BaseHub.prototype.createConnection = function (remote, local, channel) {
        throw new Error('NotImplemented');
    };

    // protected
    BaseHub.prototype.allConnections = function () {
        return this.__connPool.values();
    };

    // protected
    BaseHub.prototype.getConnection = function (remote, local) {
        return this.__connPool.get(remote, local);
    };

    // protected
    BaseHub.prototype.setConnection = function (remote, local, connection) {
        this.__connPool.set(remote, local, connection);
    };

    // protected
    BaseHub.prototype.removeConnection = function (remote, local, connection) {
        this.__connPool.remove(remote, local, connection);
    };

    //
    //  Hub
    //

    // Override
    BaseHub.prototype.connect = function (remote, local) {
        var conn = this.getConnection(remote, local);
        if (conn) {
            // check local address
            if (!local) {
                return conn;
            }
            var address = conn.getLocalAddress();
            if (!address || address.equals(local)) {
                return conn;
            }
            // local address not matched? ignore this connection
        }
        // try to open channel with direction (remote, local)
        var channel = this.open(remote, local);
        if (!channel || !channel.isOpen()) {
            return null;
        }
        // create with channel
        conn = this.createConnection(remote, local, channel);
        if (conn) {
            // NOTICE: local address in the connection may be set to null
            this.setConnection(conn.getRemoteAddress(), conn.getLocalAddress(), conn);
        }
        return conn;
    };

    //
    //  Processor
    //

    // protected
    BaseHub.prototype.driveChannel = function (channel) {
        if (!channel.isAlive()) {
            // cannot drive closed channel
            return false;
        }
        var remote = channel.getRemoteAddress();
        var local = channel.getLocalAddress();
        var conn;
        var data;
        // try to receive
        try {
            data = channel.receive(BaseHub.MSS);
        } catch (e) {
            var delegate = this.getDelegate();
            if (!delegate || !remote) {
                // UDP channel may not connected,
                // so no connection for it
                this.removeChannel(remote, local, channel);
            } else {
                // remove channel and callback with connection
                conn = this.getConnection(remote, local);
                this.removeChannel(remote, local, channel);
                if (conn) {
                    delegate.onConnectionError(e, conn);
                }
            }
            return false;
        }
        if (!data/* || data.length === 0*/) {
            // received nothing
            return false;
        }
        // get connection for processing received data
        conn = this.connect(remote, local);
        if (conn) {
            conn.onReceived(data);
        }
        return true;
    };

    // protected
    BaseHub.prototype.driveChannels = function (channels) {
        var count = 0;
        for (var i = channels.length - 1; i >= 0; --i) {
            // drive channel to receive data
            if (this.driveChannel(channels[i])) {
                ++count;
            }
        }
        return count;
    };

    // protected
    BaseHub.prototype.cleanupChannels = function (channels) {
        var sock;
        for (var i = channels.length - 1; i >= 0; --i) {
            sock = channels[i];
            if (!sock.isAlive()) {
                // if channel not connected (TCP) and not bound (UDP),
                // means it's closed, remove it from the hub
                this.removeChannel(sock.getRemoteAddress(), sock.getLocalAddress(), sock);
            }
        }
    };

    // protected
    BaseHub.prototype.driveConnections = function (connections) {
        var now = (new Date()).getTime();
        var elapsed = now - this.__last;
        for (var i = connections.length - 1; i >= 0; --i) {
            // drive connection to go on
            connections[i].tick(now, elapsed);
            // NOTICE: let the delegate to decide whether close an error connection
            //         or just remove it.
        }
        this.__last = now;
    };

    // protected
    BaseHub.prototype.cleanupConnections = function (connections) {
        var conn;
        for (var i = connections.length - 1; i >= 0; --i) {
            conn = connections[i];
            if (!conn.isOpen()) {
                // if connection closed, remove it from the hub; notice that
                // ActiveConnection can reconnect, it'll be not connected
                // but still open, don't remove it in this situation.
                this.removeConnection(conn.getRemoteAddress(), conn.getLocalAddress(), conn);
            }
        }
    };

    // Override
    BaseHub.prototype.process = function () {
        // 1. drive all channels to receive data
        var channels = this.allChannels();
        var count = this.driveChannels(channels);
        // 2. drive all connections to move on
        var connections = this.allConnections();
        this.driveConnections(connections);
        // 3. cleanup closed channels and connections
        this.cleanupChannels(channels);
        this.cleanupConnections(connections);
        return count > 0;
    };

    //-------- namespace --------
    ns.socket.BaseHub = BaseHub;

})(StarTrek, MONKEY);
