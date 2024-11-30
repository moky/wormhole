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
    var Connection        = ns.net.Connection;
    var TimedConnection   = ns.net.TimedConnection;
    var ConnectionState   = ns.net.ConnectionState;
    var StateMachine      = ns.net.ConnectionStateMachine;
    var StateOrder        = ns.net.ConnectionStateOrder;

    /**
     *  Base Connection
     *  ~~~~~~~~~~~~~~~
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     */
    var BaseConnection = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__channel = -1;     // Channel
        this.__delegate = null;  // ConnectionDelegate
        // active times
        this.__lastSentTime = null;      // Date
        this.__lastReceivedTime = null;  // Date
        // connection state machine
        this.__fsm = null;  // ConnectionStateMachine
    };
    Class(BaseConnection, AddressPairObject, [Connection, TimedConnection, ConnectionState.Delegate], {

        // Override
        toString: function () {
            var clazz   = this.getClassName();
            var remote  = this.getRemoteAddress();
            var local   = this.getLocalAddress();
            var channel = this.getChannel();
            return '<' + clazz + ' remote="' + remote + '" local="' + local + '">\n\t' +
                channel + '\n</' + clazz + '>';
        }
    });

    BaseConnection.EXPIRES = 16 * 1000;  // 16 seconds

    // delegate for handling connection events
    BaseConnection.prototype.getDelegate = function () {
        return this.__delegate;
    };
    BaseConnection.prototype.setDelegate = function (delegate) {
        this.__delegate = delegate;
    };

    //
    //  State Machine
    //

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

    //
    //  Channel
    //

    // protected
    BaseConnection.prototype.getChannel = function () {
        var channel = this.__channel;
        return channel === -1 ? null : channel;
    };
    // protected
    BaseConnection.prototype.setChannel = function (channel) {
        // 1. replace with new channel
        var old = this.__channel;
        this.__channel = channel;
        // 2. close old channel
        if (old && old !== -1 && old !== channel) {
            old.close();
        }
    };

    //
    //  Flags
    //

    // Override
    BaseConnection.prototype.isOpen = function () {
        var channel = this.__channel;
        if (channel === -1) {
            // initializing
            return true
        }
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

    // Override
    BaseConnection.prototype.isAvailable = function () {
        var channel = this.getChannel();
        return channel && channel.isAvailable();
    };

    // Override
    BaseConnection.prototype.isVacant = function () {
        var channel = this.getChannel();
        return channel && channel.isVacant();
    };

    // Override
    BaseConnection.prototype.close = function () {
        // stop state machine
        this.setStateMachine(null);
        // close channel
        this.setChannel(null);
    };

    // Get channel from hub
    BaseConnection.prototype.start = function (hub) {
        // 1. get channel from hub
        this.openChannel(hub);
        // 2. start state machine
        this.startMachine();
    };

    // protected
    BaseConnection.prototype.startMachine = function () {
        var machine = this.createStateMachine();
        this.setStateMachine(machine);
        machine.start();
    };

    // protected
    BaseConnection.prototype.openChannel = function (hub) {
        var remote = this.getRemoteAddress();
        var local = this.getLocalAddress();
        var channel = hub.open(remote, local);
        if (channel) {
            this.setChannel(channel);
        }
        return channel;
    };

    //
    //  I/O
    //

    // Override
    BaseConnection.prototype.onReceivedData = function (data) {
        this.__lastReceivedTime = new Date(); // update received time
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionReceived(data, this);
        }
    };

    // protected
    BaseConnection.prototype.doSend = function (data, destination) {
        var channel = this.getChannel();
        if (!(channel && channel.isAlive())) {
            return -1;
        } else if (!destination) {
            throw new ReferenceError('remote address should not empty')
        }
        var sent = channel.send(data, destination);
        if (sent > 0)  {
            // update sent time
            this.__lastSentTime = new Date();
        }
        return sent;
    };

    // Override
    BaseConnection.prototype.sendData = function (pack) {
        // try to send data
        var error = null
        var sent = -1;
        try {
            var destination = this.getRemoteAddress();
            sent = this.doSend(pack, destination);
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
        return !machine ? null : machine.getCurrentState();
    };

    // Override
    BaseConnection.prototype.tick = function (now, elapsed) {
        if (this.__channel === -1) {
            // not initialized
            return;
        }
        // drive state machine forward
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
        var last = this.__lastSentTime;
        last = !last ? 0 : last.getTime();
        return now.getTime() <= last + BaseConnection.EXPIRES;
    };

    // Override
    BaseConnection.prototype.isReceivedRecently = function (now) {
        var last = this.__lastReceivedTime;
        last = !last ? 0 : last.getTime();
        return now.getTime() <= last + BaseConnection.EXPIRES;
    };

    // Override
    BaseConnection.prototype.isNotReceivedLongTimeAgo = function (now) {
        var last = this.__lastReceivedTime;
        last = !last ? 0 : last.getTime();
        return now.getTime() > last + (BaseConnection.EXPIRES << 3);
    };

    //
    //  Events
    //

    // Override
    BaseConnection.prototype.enterState = function (next, ctx, now) {
        // override to process this event
    };

    // Override
    BaseConnection.prototype.exitState = function (previous, ctx, now) {
        var current = ctx.getCurrentState();
        var currentIndex = !current ? -1 : current.getIndex();
        // if current === 'ready'
        if (StateOrder.READY.equals(currentIndex)) {
            var previousIndex = !previous ? -1 : previous.getIndex();
            // if previous === 'preparing
            if (StateOrder.PREPARING.equals(previousIndex)) {
                // connection state changed from 'preparing' to 'ready',
                // set times to expired soon.
                var soon = (new Date()).getTime() - (BaseConnection.EXPIRES >> 1);
                var st = this.__lastSentTime;
                st = !st ? 0 : st.getTime();
                if (st < soon) {
                    this.__lastSentTime = new Date(soon);
                }
                var rt = this.__lastReceivedTime;
                rt = !rt ? 0 : rt.getTime();
                if (rt < soon) {
                    this.__lastReceivedTime = new Date(soon);
                }
            }
        }
        // callback
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionStateChanged(previous, current, this);
        }
        // if current == 'error'
        if (StateOrder.ERROR.equals(currentIndex)) {
            // remove channel when error
            this.setChannel(null);
        }
    };

    // Override
    BaseConnection.prototype.pauseState = function (current, ctx, now) {
        // override to process this event
    };

    // Override
    BaseConnection.prototype.resumeState = function (current, ctx, now) {
        // override to process this event
    };

    //-------- namespace --------
    ns.socket.BaseConnection = BaseConnection;

})(StarTrek, MONKEY);

(function (ns, fsm, sys) {
    'use strict';

    var Class = sys.type.Class;
    var Runnable = fsm.skywalker.Runnable;
    var Thread   = fsm.threading.Thread;
    var BaseConnection = ns.socket.BaseConnection;

    /**
     *  Active Connection
     *  ~~~~~~~~~~~~~~~~~
     *  for client
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     */
    var ActiveConnection = function (remote, local) {
        BaseConnection.call(this, remote, local);
        this.__hub = null;
        // background threading
        this.__thread = null;
        this.__bg_next_loop = 0;
        this.__bg_expired = 0;
        this.__bg_last_time = 0;
        this.__bg_interval = 8000;
    };
    Class(ActiveConnection, BaseConnection, [Runnable], {
        
        // Override
        isOpen: function () {
            return this.getStateMachine() !== null;
        },
        
        // Override
        start: function (hub) {
            this.__hub = hub;
            // 1. start state machine
            this.startMachine();
            // 2. start a background thread to check channel
            var thread = this.__thread;
            if (thread) {
                this.__thread = null;
                thread.stop();
            }
            thread = new Thread(this);
            thread.start();
            this.__thread = thread;
        },
        
        // Override
        run: function () {
            var now = (new Date()).getTime();
            if (this.__bg_next_loop === 0) {
                // first loop, set the clock
                this.__bg_next_loop = now + 1000;
                return true;
            } else if (this.__bg_next_loop > now) {
                // sleeping
                return true;
            } else {
                // reset the clock before enter the loop
                this.__bg_next_loop = now + 1000;
            }
            if (!this.isOpen()) {
                return false; // break
            }
            try {
                var channel = this.getChannel();
                if (!(channel && channel.isOpen())) {
                    // first time to try connecting (lastTime == 0)?
                    // or connection lost, then try to reconnect again.
                    // check time interval for the trying here
                    if (now < this.__bg_last_time + this.__bg_interval) {
                        return true; // continue
                    } else {
                        // update last connect time
                        this.__bg_last_time = now;
                    }
                    // get new socket channel via hub
                    var hub = this.__hub;
                    if (!hub) {
                        // hub not found
                        return false; // break
                    }
                    // try to open a new socket channel from the hub.
                    // the returned socket channel is opened for connecting,
                    // but maybe failed,
                    // so set an expired time to close it after timeout;
                    // if failed to open a new socket channel,
                    // then extend the time interval for next trying.
                    channel = this.openChannel(hub);
                    if (channel) {
                        // connect timeout after 2 minutes
                        this.__bg_expired = now + 128000;
                    } else if (this.__bg_interval < 128000) {
                        this.__bg_interval <<= 1;
                    }
                } else if (channel.isAlive()) {
                    // socket channel is normal, reset the time interval here.
                    // this will work when the current connection lost
                    this.__bg_interval = 8000;
                } else if (0 < this.__bg_expired && this.__bg_expired < now) {
                    // connect timeout
                    channel.close();
                }
            } catch (e) {
                // console.error('ActiveConnection Error', e, this);
                var delegate = this.getDelegate();
                if (delegate) {
                    delegate.onConnectionError(e, this);
                }
            }
            return true; // continue
        }
    });

    //-------- namespace --------
    ns.socket.ActiveConnection = ActiveConnection;

})(StarTrek, FiniteStateMachine, MONKEY);
