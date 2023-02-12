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
//! require 'net/channel.js'

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;

    var SocketReader = Interface(null, null);

    /**
     *  Read data from socket
     *
     * @param {uint} maxLen - max length of received data
     * @return {Uint8Array} received data
     */
    SocketReader.prototype.read = function (maxLen) {
        throw new Error('NotImplemented');
    };

    /**
     *  Receive data from socket
     *
     * @param {uint} maxLen - max length of received data
     * @return {Uint8Array} received data
     */
    SocketReader.prototype.receive = function (maxLen) {
        throw new Error('NotImplemented');
    };

    var SocketWriter = Interface(null, null);

    /**
     *  Write data into socket
     *
     * @param {Uint8Array} src - data to be wrote
     * @return {int} -1 on error
     */
    SocketWriter.prototype.write = function (src) {
        throw new Error('NotImplemented');
    };

    /**
     *  Send data via socket with remote address
     *
     * @param {Uint8Array} src       - data to send
     * @param {SocketAddress} target - remote address
     * @return {int} sent length, -1 on error
     */
    SocketWriter.prototype.send = function (src, target) {
        throw new Error('NotImplemented');
    };

    //-------- namespace --------
    ns.socket.SocketReader = SocketReader;
    ns.socket.SocketWriter = SocketWriter;

})(StarTrek, MONKEY);

/**
 *  WebSocket Wrapper
 *  ~~~~~~~~~~~~~~~~~
 *
 *  Socket = {
 *      configureBlocking: function(block) {},
 *
 *      isBlocking:  function() {return false},
 *      isOpen:      function() {return true},
 *      isConnected: function() {return true},
 *      isBound:     function() {return true},
 *      isAlive:     function() {return true},
 *
 *      getRemoteAddress: function() {return remote},
 *      getLocalAddress:  function() {return local},
 *
 *      bind:    function(local)  {return ws},
 *      connect: function(remote) {return ws},
 *      close:   function()       {ws.close()},
 *
 *      read:    function(maxLen)       {return new Uint8Array(maxLen)},
 *      write:   function(data)         {return data.length},
 *      receive: function(maxLen)       {return new Uint8Array(maxLen)},
 *      send:    function(data, remote) {return data.length}
 *  }
 */

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var AddressPairObject = ns.type.AddressPairObject;
    var Channel = ns.net.Channel;

    /**
     *  Base Channel
     *  ~~~~~~~~~~~~
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     * @param {WebSocket|*} sock     - WebSocket wrapper
     */
    var BaseChannel = function (remote, local, sock) {
        AddressPairObject.call(this, remote, local);
        this.__sock = sock;
        // socket reader/writer
        this.__reader = this.createReader();
        this.__writer = this.createWriter();
        // flags
        this.__blocking = false;
        this.__opened = false;
        this.__connected = false;
        this.__bound = false;
        this.refreshFlags();
    };
    Class(BaseChannel, AddressPairObject, [Channel], null);

    // destroy()
    BaseChannel.prototype.finalize = function () {
        // make sure the relative socket is removed
        removeSocketChannel.call(this);
        // super.finalize();
    };

    /**
     *  Create socket reader
     */
    // protected
    BaseChannel.prototype.createReader = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Create socket writer
     */
    // protected
    BaseChannel.prototype.createWriter = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Refresh flags with inner socket
     */
    // protected
    BaseChannel.prototype.refreshFlags = function () {
        var sock = this.__sock;
        if (sock) {
            this.__blocking = sock.isBlocking();
            this.__opened = sock.isOpen();
            this.__connected = sock.isConnected();
            this.__bound = sock.isBound();
        } else {
            this.__blocking = false;
            this.__opened = false;
            this.__connected = false;
            this.__bound = false;
        }
    };

    /**
     *  Get inner socket
     *
     * @return {WebSocket|*} WebSocket wrapper
     */
    BaseChannel.prototype.getSocket = function () {
        return this.__sock;
    };

    var removeSocketChannel = function () {
        // 1. clear inner channel
        var old = this.__sock;
        this.__sock = null;
        // 2. refresh flags
        this.refreshFlags();
        // 3. close old channel
        if (old && old.isOpen()) {
            old.clone();
        }
    };

    // Override
    BaseChannel.prototype.configureBlocking = function (block) {
        var sock = this.getSocket();
        sock.configureBlocking(block);
        this.__blocking = block;
        return sock;
    };

    // Override
    BaseChannel.prototype.isBlocking = function () {
        return this.__blocking;
    };

    // Override
    BaseChannel.prototype.isOpen = function () {
        return this.__opened;
    };

    // Override
    BaseChannel.prototype.isConnected = function () {
        return this.__connected;
    };

    // Override
    BaseChannel.prototype.isBound = function () {
        return this.__bound;
    };

    // Override
    BaseChannel.prototype.isAlive = function () {
        return this.isOpen() && (this.isConnected() || this.isBound());
    };

    // Override
    BaseChannel.prototype.bind = function (local) {
        if (!local) {
            local = this.localAddress;
        }
        var sock = this.getSocket();
        var nc = sock.bind(local);
        this.localAddress = local;
        this.__bound = true;
        this.__opened = true;
        this.__blocking = sock.isBlocking();
        return nc;
    };

    // Override
    BaseChannel.prototype.connect = function (remote) {
        if (!remote) {
            remote = this.remoteAddress;
        }
        var sock = this.getSocket();
        sock.connect(remote);
        this.remoteAddress = remote;
        this.__connected = true;
        this.__opened = true;
        this.__blocking = sock.isBlocking();
        return sock;
    };

    // Override
    BaseChannel.prototype.disconnect = function () {
        var sock = this.__sock;
        removeSocketChannel.call(this);
        return sock;
    };

    // Override
    BaseChannel.prototype.close = function () {
        // close inner socket and refresh flags
        removeSocketChannel.call(this);
    };

    //
    //  Input/Output
    //

    // Override
    BaseChannel.prototype.read = function (maxLen) {
        try {
            return this.__reader.read(maxLen);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    // Override
    BaseChannel.prototype.write = function (src) {
        try {
            return this.__writer.write(src);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    // Override
    BaseChannel.prototype.receive = function (maxLen) {
        try {
            return this.__reader.receive(maxLen);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    // Override
    BaseChannel.prototype.send = function (src, target) {
        try {
            return this.__writer.send(src, target);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    //-------- namespace --------
    ns.socket.BaseChannel = BaseChannel;

})(StarTrek, MONKEY);
