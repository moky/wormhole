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
//! require 'net/machine.js'

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var AddressPairObject = ns.type.AddressPairObject;
    var Connection = ns.net.Connection;
    var TimedConnection = ns.net.TimedConnection;
    var ConnectionState = ns.net.ConnectionState;
    var StateMachine = ns.net.StateMachine;

    /**
     *  Base Connection
     *  ~~~~~~~~~~~~~~~
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     * @param {Channel} channel
     */
    var BaseConnection = function (remote, local, channel) {
        AddressPairObject.call(this, remote, local);
        this.__channel = channel;
        this.__delegate = null;
        // active times
        this.__lastSentTime = 0;
        this.__lastReceivedTime = 0;
        // connection state machine
        this.__fsm = null;
    };
    Class(BaseConnection, AddressPairObject, [Connection, TimedConnection, ConnectionState.Delegate], null);

    BaseConnection.EXPIRES = 16 * 1000;  // 16 seconds

    // destroy()
    BaseConnection.prototype.finalize = function () {
        // make sure the relative channel is closed
        this.setChannel(null);
        this.setStateMachine(null);
        // super.finalize();
    };

    // protected
    BaseConnection.prototype.getStateMachine = function () {
        return this.__fsm;
    };
    // private
    BaseConnection.prototype.setStateMachine = function (machine) {
        // 1. replace with new machine
        var old = this.__fsm;
        this.__fsm = machine;
        // 2. stop old machine
        if (old && old !== machine) {
            old.stop();
        }
    };
    // protected
    BaseConnection.prototype.createStateMachine = function () {
        var machine = new StateMachine(this);
        machine.setDelegate(this);
        return machine;
    };

    // protected
    BaseConnection.prototype.getDelegate = function () {
        return this.__delegate;
    };
    // public: delegate for handling connection events
    BaseConnection.prototype.setDelegate = function (delegate) {
        this.__delegate = delegate;
    };

    // protected
    BaseConnection.prototype.getChannel = function () {
        return this.__channel;
    };
    // protected
    BaseConnection.prototype.setChannel = function (channel) {
        // 1. replace with new channel
        var old = this.__channel;
        this.__channel = channel;
        // 2. close old channel
        if (old && old !== channel) {
            if (old.isConnected()) {
                try {
                    old.disconnect();
                } catch (e) {
                    console.error('BaseConnection::setChannel()', e, old);
                }
            }
        }
    };

    // Override
    BaseConnection.prototype.isOpen = function () {
        var channel = this.getChannel();
        return channel && channel.isOpen();
    };

    // Override
    BaseConnection.prototype.isBound = function () {
        var channel = this.getChannel();
        return channel && channel.isBound();
    };

    // Override
    BaseConnection.prototype.isConnected = function () {
        var channel = this.getChannel();
        return channel && channel.isConnected();
    };

    // Override
    BaseConnection.prototype.isAlive = function () {
        // var channel = this.getChannel();
        // return channel && channel.isAlive();
        return this.isOpen() && (this.isConnected() || this.isBound());
    };

    /*/
    // Override
    BaseConnection.prototype.getLocalAddress = function () {
        var channel = this.getChannel();
        return channel ? channel.getLocalAddress() : this.localAddress;
    };
    /*/

    // Override
    BaseConnection.prototype.clone = function () {
        this.setChannel(null);
        this.setStateMachine(null);
    };

    BaseConnection.prototype.start = function () {
        var machine = this.createStateMachine();
        machine.start();
        this.setStateMachine(machine);
    };

    BaseConnection.prototype.stop = function () {
        this.setChannel(null);
        this.setStateMachine(null);
    };

    //
    //  I/O
    //

    // Override
    BaseConnection.prototype.onReceived = function (data) {
        this.__lastReceivedTime = (new Date()).getTime(); // update received time
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionReceived(data, this);
        }
    };

    // protected
    BaseConnection.prototype.sendTo = function (data, destination) {
        var sent = -1;
        var channel = this.getChannel();
        if (channel && channel.isAlive()) {
            sent = channel.send(data, destination);
            if (sent > 0)  {
                // update sent time
                this.__lastSentTime = (new Date()).getTime();
            }
        }
        return sent;
    };

    // Override
    BaseConnection.prototype.send = function (pack) {
        // try to send data
        var error = null
        var sent = -1;
        try {
            var destination = this.getRemoteAddress();
            sent = this.sendTo(pack, destination);
            if (sent < 0) {  // == -1
                error = new Error('failed to send data: ' + pack.length + ' byte(s) to ' + destination);
            }
        } catch (e) {
            error = e;
            // socket error, close current channel
            this.setChannel(null);
        }
        // callback
        var delegate = this.getDelegate();
        if (delegate) {
            if (error) {
                delegate.onConnectionFailed(error, pack, this);
            } else {
                delegate.onConnectionSent(sent, pack, this);
            }
        }
        return sent;
    };

    //
    //  Status
    //

    // Override
    BaseConnection.prototype.getState = function () {
        var machine = this.getStateMachine();
        return machine ? machine.getCurrentState() : null;
    };

    // Override
    BaseConnection.prototype.tick = function (now, elapsed) {
        var machine = this.getStateMachine();
        if (machine) {
            machine.tick(now, elapsed);
        }
    };

    //
    //  Timed
    //

    // Override
    BaseConnection.prototype.getLastSentTime = function () {
        return this.__lastSentTime;
    };

    // Override
    BaseConnection.prototype.getLastReceivedTime = function () {
        return this.__lastReceivedTime;
    };

    // Override
    BaseConnection.prototype.isSentRecently = function (now) {
        return now <= this.__lastSentTime + BaseConnection.EXPIRES;
    };

    // Override
    BaseConnection.prototype.isReceivedRecently = function (now) {
        return now <= this.__lastReceivedTime + BaseConnection.EXPIRES;
    };

    // Override
    BaseConnection.prototype.isNotReceivedLongTimeAgo = function (now) {
        return now > this.__lastSentTime + (BaseConnection.EXPIRES << 3);
    };

    //
    //  Events
    //

    // Override
    BaseConnection.prototype.enterState = function (next, machine) {
        // override to process this event
    };

    // Override
    BaseConnection.prototype.exitState = function (previous, machine) {
        var current = machine.getCurrentState();
        // if current === 'ready'
        if (current && current.equals(ConnectionState.READY)) {
            // if previous === 'preparing
            if (previous && previous.equals(ConnectionState.PREPARING)) {
                // connection state changed from 'preparing' to 'ready',
                // set times to expired soon.
                var timestamp = (new Date()).getTime() - (BaseConnection.EXPIRES >> 1);
                if (this.__lastSentTime < timestamp) {
                    this.__lastSentTime = timestamp;
                }
                if (this.__lastReceivedTime < timestamp) {
                    this.__lastReceivedTime = timestamp;
                }
            }
        }
        // callback
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionStateChanged(previous, current, this);
        }
    };

    // Override
    BaseConnection.prototype.pauseState = function (current, machine) {
        // override to process this event
    };

    // Override
    BaseConnection.prototype.resumeState = function (current, machine) {
        // override to process this event
    };

    //-------- namespace --------
    ns.socket.BaseConnection = BaseConnection;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var BaseConnection = ns.socket.BaseConnection;

    /**
     *  Active Connection
     *  ~~~~~~~~~~~~~~~~~
     *  for client
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     * @param {Channel} channel
     * @param {Hub} hub
     */
    var ActiveConnection = function (remote, local, channel, hub) {
        BaseConnection.call(this, remote, local, channel);
        this.__hub = hub;
    };
    Class(ActiveConnection, BaseConnection, null, {
        // Override
        isOpen: function () {
            return this.getStateMachine() !== null;
        },
        // Override
        getChannel: function () {
            var channel = BaseConnection.prototype.getChannel.call(this);
            if (!channel || !channel.isOpen()) {
                if (this.getStateMachine() === null) {
                    // closed (not start yet)
                    return null;
                }
                // get new channel via hub
                this.__hub.open(this.remoteAddress, this.localAddress);
                this.setChannel(channel);
            }
            return channel;
        }
    })

    //-------- namespace --------
    ns.socket.ActiveConnection = ActiveConnection;

})(StarTrek, MONKEY);
