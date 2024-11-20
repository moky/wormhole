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
//! require 'controller.js'

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
    var Channel           = ns.net.Channel;
    var ChannelStateOrder = ns.net.ChannelStateOrder;
    var SocketHelper      = ns.net.SocketHelper;

    /**
     *  Base Channel
     *  ~~~~~~~~~~~~
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     */
    var BaseChannel = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        // SocketReader, SocketWriter
        this.__reader = this.createReader();
        this.__writer = this.createWriter();
        // inner socket
        this.__sock = null;  // WebSocket wrapper
        this.__closed = -1;  // 0: false, 1: true
    };
    Class(BaseChannel, AddressPairObject, [Channel], {

        // Override
        toString: function () {
            var clazz     = this.getClassName();
            var remote    = this.getRemoteAddress();
            var local     = this.getLocalAddress();
            var closed   = !this.isOpen();
            var bound     = this.isBound();
            var connected = this.isConnected();
            var sock      = this.getSocket();
            return '<' + clazz + ' remote="' + remote + '" local="' + local + '"' +
                ' closed=' + closed + ' bound=' + bound + ' connected=' + connected + '>\n\t' +
                sock + '\n</' + clazz + '>';
        }
    });

    // create socket reader & writer
    BaseChannel.prototype.createReader = function () {};
    BaseChannel.prototype.createWriter = function () {};
    // protected
    BaseChannel.prototype.getReader = function () {
        return this.__reader;
    };
    BaseChannel.prototype.getWriter = function () {
        return this.__writer;
    };

    //
    //  Socket
    //

    BaseChannel.prototype.getSocket = function () {
        return this.__sock;
    };

    /**
     *  Set inner socket for this channel
     *
     * @param {WebSocket} sock
     */
    BaseChannel.prototype.setSocket = function (sock) {
        // 1. replace with new socket
        var old = this.__sock;
        if (sock) {
            this.__sock = sock;
            this.__closed = 0;
        } else {
            this.__sock = null;
            this.__closed = 1;
        }
        // 2. close old socket
        if (old && old !== sock) {
            SocketHelper.socketDisconnect(old);
        }
    };

    //
    //  States
    //

    // Override
    BaseChannel.prototype.getState = function () {
        if (this.__closed < 0) {
            // initializing
            return ChannelStateOrder.INIT;
        }
        var sock = this.getSocket();
        if (!sock || SocketHelper.socketIsClosed(sock)) {
            // closed
            return ChannelStateOrder.CLOSED;
        } else if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
            // normal
            return ChannelStateOrder.ALIVE;
        } else {
            // opened
            return ChannelStateOrder.OPEN;
        }
    };

    // Override
    BaseChannel.prototype.isOpen = function () {
        if (this.__closed < 0) {
            // initializing
            return true;
        }
        var sock = this.getSocket();
        return sock && !SocketHelper.socketIsClosed(sock);
    };

    // Override
    BaseChannel.prototype.isBound = function () {
        var sock = this.getSocket();
        return sock && SocketHelper.socketIsBound(sock);
    };

    // Override
    BaseChannel.prototype.isConnected = function () {
        var sock = this.getSocket();
        return sock && SocketHelper.socketIsConnected(sock);
    };

    // Override
    BaseChannel.prototype.isAlive = function () {
        return this.isOpen() && (this.isConnected() || this.isBound());
    };

    // Override
    BaseChannel.prototype.isAvailable = function () {
        var sock = this.getSocket();
        if (!sock || SocketHelper.socketIsClosed(sock)) {
            return false;
        } else if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
            // alive, check reading buffer
            return this.checkAvailable(sock);
        } else {
            return false;
        }
    };

    // protected
    BaseChannel.prototype.checkAvailable = function (sock) {
        return SocketHelper.socketIsAvailable(sock);
    };

    // Override
    BaseChannel.prototype.isVacant = function () {
        var sock = this.getSocket();
        if (!sock || SocketHelper.socketIsClosed(sock)) {
            return false;
        } else if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
            // alive, check writing buffer
            return this.checkVacant(sock);
        } else {
            return false;
        }
    };

    // protected
    BaseChannel.prototype.checkVacant = function (sock) {
        return SocketHelper.socketIsVacant(sock);
    };

    // Override
    BaseChannel.prototype.isBlocking = function () {
        var sock = this.getSocket();
        return sock && SocketHelper.socketIsBlocking(sock);
    };

    // Override
    BaseChannel.prototype.configureBlocking = function (block) {
        var sock = this.getSocket();
        sock.configureBlocking(block);
        return sock;
    };

    // protected
    BaseChannel.prototype.doBind = function (sock, local) {
        return SocketHelper.socketBind(sock, local);
    };

    // protected
    BaseChannel.prototype.doConnect = function (sock, remote) {
        return SocketHelper.socketConnect(sock, remote);
    };

    // protected
    BaseChannel.prototype.doDisconnect = function (sock) {
        return SocketHelper.socketDisconnect(sock);
    };

    // Override
    BaseChannel.prototype.bind = function (local) {
        var sock = this.getSocket();
        if (sock) {
            this.doBind(sock, local);
        }
        this.localAddress = local;
        return sock;
    };

    // Override
    BaseChannel.prototype.connect = function (remote) {
        var sock = this.getSocket();
        if (sock) {
            this.doConnect(sock, remote);
        }
        this.remoteAddress = remote;
        return sock;
    };

    // Override
    BaseChannel.prototype.disconnect = function () {
        var sock = this.getSocket();
        if (sock) {
            this.doDisconnect(sock);
        }
        return sock;
    };

    // Override
    BaseChannel.prototype.close = function () {
        this.setSocket(null);
    };

    //
    //  Reading, Writing
    //

    // Override
    BaseChannel.prototype.read = function (maxLen) {
        try {
            return this.getReader().read(maxLen);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    // Override
    BaseChannel.prototype.write = function (src) {
        try {
            return this.getWriter().write(src);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    // Override
    BaseChannel.prototype.receive = function (maxLen) {
        try {
            return this.getReader().receive(maxLen);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    // Override
    BaseChannel.prototype.send = function (src, target) {
        try {
            return this.getWriter().send(src, target);
        } catch (e) {
            this.close();
            throw e;
        }
    };

    //-------- namespace --------
    ns.socket.BaseChannel = BaseChannel;

})(StarTrek, MONKEY);
