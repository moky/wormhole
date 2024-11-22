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

//! require 'namespace.js'

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;
    var Enum      = sys.type.Enum;

    // protected
    var ChannelStateOrder = Enum(null, {
        INIT:   0,  // initializing
        OPEN:   1,  // initialized
        ALIVE:  2,  // (not closed) and (connected or bound)
        CLOSED: 3   // closed
    });

    var Channel = Interface(null, null);

    // Channel State Order
    Channel.prototype.getState = function () {};

    Channel.prototype.isOpen = function () {};

    Channel.prototype.isBound = function () {};

    // this.isOpen() && (this.isConnected() || this.isBound());
    Channel.prototype.isAlive = function () {};

    // ready for reading
    Channel.prototype.isAvailable = function () {};  // isAlive

    // ready for writing
    Channel.prototype.isVacant = function () {};  // isAlive

    Channel.prototype.close = function () {};


    /*================================================*\
    |*          Readable Byte Channel                 *|
    \*================================================*/

    /**
     *  Read data from channel
     *
     * @param {uint} maxLen - max length of received data
     * @return {Uint8Array} received data
     */
    Channel.prototype.read = function (maxLen) {};


    /*================================================*\
    |*          Writable Byte Channel                 *|
    \*================================================*/

    /**
     *  Write data into channel
     *
     * @param {Uint8Array} src - data to be wrote
     * @return {int} -1 on error
     */
    Channel.prototype.write = function (src) {};


    /*================================================*\
    |*          Selectable Channel                    *|
    \*================================================*/

    /**
     *  Adjusts this channel's blocking mode.
     *
     * @param {boolean} block
     * @return {WebSocket|*} the inner SelectableChannel
     */
    Channel.prototype.configureBlocking = function (block) {};

    /**
     *  Tells whether or not every I/O operation on this channel will block
     *  until it completes.  A newly-created channel is always in blocking mode.
     *
     * @return {boolean} true when this channel is in blocking mode
     */
    Channel.prototype.isBlocking = function () {};


    /*================================================*\
    |*          Network Channel                       *|
    \*================================================*/

    /**
     *  Binds the channel's socket to a local address.
     *
     * @param {SocketAddress} local
     * @return {WebSocket|*} the inner NetworkChannel
     */
    Channel.prototype.bind = function (local) {};

    /**
     *  Get local address that this channel's socket is bound to.
     *
     * @return {SocketAddress} local address
     */
    Channel.prototype.getLocalAddress = function () {};


    /*================================================*\
    |*          Socket/Datagram Channel               *|
    \*================================================*/

    /**
     *  Check whether this channel's network socket is connected.
     *
     * @return {boolean}
     */
    Channel.prototype.isConnected = function () {};

    /**
     *  Connect to remote address
     *
     * @param {SocketAddress} remote - remote address
     * @return {WebSocket|*} the inner NetworkChannel; null on failed
     */
    Channel.prototype.connect = function (remote) {};

    /**
     *  Get remote address to which this channel's socket is connected.
     *
     * @return {SocketAddress} remote address
     */
    Channel.prototype.getRemoteAddress = function () {};


    /*================================================*\
    |*          Datagram Channel                      *|
    \*================================================*/

    /**
     *  Disconnects this channel's socket.
     *
     * @return {WebSocket|*} the inner ByteChannel
     */
    Channel.prototype.disconnect = function () {};

    /**
     *  Receives a datagram via this channel.
     *
     * @param {uint} maxLen
     * @return {Uint8Array} received data package
     */
    Channel.prototype.receive = function (maxLen) {};

    /**
     *  Sends a datagram via this channel.
     *
     * @param {Uint8Array} src       - data package to be sent
     * @param {SocketAddress} target - remote address
     * @return {int} the number of bytes sent, -1 on error
     */
    Channel.prototype.send = function (src, target) {};

    //-------- namespace --------
    ns.net.Channel           = Channel;
    ns.net.ChannelStateOrder = ChannelStateOrder;

})(StarTrek, MONKEY);

(function (ns) {
    'use strict';

    //-------- namespace --------
    ns.net.SocketHelper = {

        //
        //  Socket Channels
        //

        socketGetLocalAddress: function (sock) {
            return sock.getRemoteAddress();
        },
        socketGetRemoteAddress: function (sock) {
            return sock.getLocalAddress();
        },

        //
        //  Flags
        //

        socketIsBlocking: function (sock) {
            return sock.isBlocking();
        },
        socketIsConnected: function (sock) {
            return sock.isConnected();
            // return sock.readyState === WebSocket.OPEN;
        },
        socketIsBound: function (sock) {
            return sock.isBound();
            // return sock.localAddress !== null;
        },
        socketIsClosed: function (sock) {
            return !sock.isOpen();
            // return sock.readyState === WebSocket.CLOSED;
        },

        // Ready for reading
        socketIsAvailable: function (sock) {
            // TODO: check reading buffer
            return sock.isAlive();
            // return sock.readyState === WebSocket.OPEN;
        },
        // Ready for writing
        socketIsVacant: function (sock) {
            // TODO: check writing buffer
            return sock.isAlive();
            // return sock.readyState === WebSocket.OPEN;
        },

        //
        //  Async Socket I/O
        //

        socketSend: function (sock, data) {
            return sock.write(data);
        },
        socketReceive: function (sock, maxLen) {
            return sock.read(maxLen);
        },

        // Bind to local address
        socketBind: function (sock, local) {
            return sock.bind(local);
        },
        // Connect to remote address
        socketConnect: function (sock, remote) {
            return sock.connect(remote);
        },

        //  Close socket
        socketDisconnect: function (sock) {
            return sock.close();
        }
    }

})(StarTrek);
