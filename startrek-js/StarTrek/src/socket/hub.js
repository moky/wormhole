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
//! require 'net/hub.js'

    st.socket.ConnectionPool = function () {
        AddressPairMap.call(this);
    };
    var ConnectionPool = st.socket.ConnectionPool;

    Class(ConnectionPool, AddressPairMap, null, {

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
     *  Base Hub
     *  ~~~~~~~~
     *
     * @param {ConnectionDelegate} gate
     */
    st.socket.BaseHub = function (gate) {
        BaseObject.call(this);
        this.__delegate = gate;
        this.__connPool = this.createConnectionPool();
        // last time drove connections
        this.__last = new Date();
    };
    var BaseHub = st.socket.BaseHub;

    Class(BaseHub, BaseObject, [Hub], null);

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
    BaseHub.prototype.allChannels = function () {};

    /**
     *  Remove socket channel
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     * @param {Channel} channel
     */
    // protected
    BaseHub.prototype.removeChannel = function (remote, local, channel) {};

    //
    //  Connections
    //

    /**
     *  Create connection with socket channel & addresses
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     * @return {Connection}
     */
    // protected
    BaseHub.prototype.createConnection = function (remote, local) {};

    // protected
    BaseHub.prototype.allConnections = function () {
        return this.__connPool.items();
    };

    // protected
    BaseHub.prototype.getConnection = function (remote, local) {
        return this.__connPool.get(remote, local);
    };

    // protected
    BaseHub.prototype.setConnection = function (remote, local, connection) {
        return this.__connPool.set(remote, local, connection);
    };

    // protected
    BaseHub.prototype.removeConnection = function (remote, local, connection) {
        return this.__connPool.remove(remote, local, connection);
    };

    //
    //  Hub
    //

    // Override
    BaseHub.prototype.connect = function (remote, local) {
        //
        //  0. pre-checking
        //
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
        }
        //
        //  1. create new connection & cache it
        //
        conn = this.createConnection(remote, local);
        if (!local) {
            local = conn.getLocalAddress();
        }
        // cache the connection
        var cached = this.setConnection(remote, local, conn);
        if (cached && cached !== conn) {
            cached.close();
        }
        //
        //  2. start the new connection
        //
        if (conn instanceof BaseConnection) {
            // try to open channel with direction (remote, local)
            conn.start(this);
        }
        return conn;
    };

    //
    //  Processor
    //

    // protected
    BaseHub.prototype.closeChannel = function (channel) {
        try {
            if (channel.isOpen()) {
                channel.close();
            }
        } catch (e) {
            // console.error(this, 'close channel error', e, this);
        }
    };

    // protected
    BaseHub.prototype.driveChannel = function (channel) {
        //
        //  0. check channel state
        //
        var cs = channel.getState();
        if (StateOrder.INIT.equals(cs)) {
            // preparing
            return false;
        } else if (StateOrder.CLOSED.equals(cs)) {
            // finished
            return false;
        }
        // cs == opened
        // cs == alive
        var conn;
        var remote;
        var local;
        var data;           // Uint8Array
        //
        //  1. try to receive
        //
        try {
            var pair = channel.receive(BaseHub.MSS);
            data = pair.a;
            remote = pair.b;
        } catch (e) {
            remote = channel.getRemoteAddress();
            local = channel.getLocalAddress();
            var gate = this.getDelegate();
            var cached;
            if (!gate || !remote) {
                // UDP channel may not connected,
                // so no connection for it
                cached = this.removeChannel(remote, local, channel);
            } else {
                // remove channel and callback with connection
                conn = this.getConnection(remote, local);
                cached = this.removeChannel(remote, local, channel);
                if (conn) {
                    gate.onConnectionError(e, conn);
                }
            }
            if (cached && cached !== channel) {
                this.closeChannel(cached);
            }
            this.closeChannel(channel);
            return false;
        }
        if (!remote || !data/* || data.length === 0*/) {
            // received nothing
            return false;
        } else {
            local = channel.getLocalAddress();
        }
        //
        //  2. get connection for processing received data
        //
        conn = this.connect(remote, local);
        if (conn) {
            conn.onReceivedData(data);
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
        var cached, sock;   // Channel
        var remote, local;  // SocketAddress
        for (var i = channels.length - 1; i >= 0; --i) {
            sock = channels[i];
            if (!sock.isOpen()) {
                // if channel not connected (TCP) and not bound (UDP),
                // means it's closed, remove it from the hub
                remote = sock.getRemoteAddress();
                local = sock.getLocalAddress();
                cached = this.removeChannel(remote, local, sock);
                if (cached && cached !== sock) {
                    this.closeChannel(cached);
                }
            }
        }
    };

    // protected
    BaseHub.prototype.driveConnections = function (connections) {
        var now = new Date();
        var elapsed = Duration.between(this.__last, now);
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
        var cached, conn;   // Connection
        var remote, local;  // SocketAddress
        for (var i = connections.length - 1; i >= 0; --i) {
            conn = connections[i];
            if (!conn.isOpen()) {
                // if connection closed, remove it from the hub; notice that
                // ActiveConnection can reconnect, it'll be not connected
                // but still open, don't remove it in this situation.
                remote = conn.getRemoteAddress();
                local = conn.getLocalAddress();
                cached = this.removeConnection(remote, local, conn);
                if (cached && cached !== conn) {
                    cached.close();
                }
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
