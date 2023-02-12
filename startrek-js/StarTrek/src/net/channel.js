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

    var Channel = Interface(null, null);

    Channel.prototype.isOpen = function () {
        throw new Error('NotImplemented');
    };

    Channel.prototype.isBound = function () {
        throw new Error('NotImplemented');
    };

    Channel.prototype.isAlive = function () {
        // return this.isOpen() && (this.isConnected() || this.isBound());
        throw new Error('NotImplemented');
    };

    Channel.prototype.close = function () {
        throw new Error('NotImplemented');
    };


    /*================================================*\
    |*          Readable Byte Channel                 *|
    \*================================================*/

    /**
     *  Read data from channel
     *
     * @param {uint} maxLen - max length of received data
     * @return {Uint8Array} received data
     */
    Channel.prototype.read = function (maxLen) {
        throw new Error('NotImplemented');
    };


    /*================================================*\
    |*          Writable Byte Channel                 *|
    \*================================================*/

    /**
     *  Write data into channel
     *
     * @param {Uint8Array} src - data to be wrote
     * @return {int} -1 on error
     */
    Channel.prototype.write = function (src) {
        throw new Error('NotImplemented');
    };


    /*================================================*\
    |*          Selectable Channel                    *|
    \*================================================*/

    /**
     *  Adjusts this channel's blocking mode.
     *
     * @param {boolean} block
     * @return {WebSocket|*} the inner SelectableChannel
     */
    Channel.prototype.configureBlocking = function (block) {
        throw new Error('NotImplemented');
    };

    /**
     *  Tells whether or not every I/O operation on this channel will block
     *  until it completes.  A newly-created channel is always in blocking mode.
     *
     * @return {boolean} true when this channel is in blocking mode
     */
    Channel.prototype.isBlocking = function () {
        throw new Error('NotImplemented');
    };


    /*================================================*\
    |*          Network Channel                       *|
    \*================================================*/

    /**
     *  Binds the channel's socket to a local address.
     *
     * @param {SocketAddress} local
     * @return {WebSocket|*} the inner NetworkChannel
     */
    Channel.prototype.bind = function (local) {
        throw new Error('NotImplemented');
    };

    /**
     *  Get local address that this channel's socket is bound to.
     *
     * @return {SocketAddress} local address
     */
    Channel.prototype.getLocalAddress = function () {
        throw new Error('NotImplemented');
    };


    /*================================================*\
    |*          Socket/Datagram Channel               *|
    \*================================================*/

    /**
     *  Check whether this channel's network socket is connected.
     *
     * @return {boolean}
     */
    Channel.prototype.isConnected = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Connect to remote address
     *
     * @param {SocketAddress} remote - remote address
     * @return {WebSocket|*} the inner NetworkChannel; null on failed
     */
    Channel.prototype.connect = function (remote) {
        throw new Error('NotImplemented');
    };

    /**
     *  Get remote address to which this channel's socket is connected.
     *
     * @return {SocketAddress} remote address
     */
    Channel.prototype.getRemoteAddress = function () {
        throw new Error('NotImplemented');
    };


    /*================================================*\
    |*          Datagram Channel                      *|
    \*================================================*/

    /**
     *  Disconnects this channel's socket.
     *
     * @return {WebSocket|*} the inner ByteChannel
     */
    Channel.prototype.disconnect = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Receives a datagram via this channel.
     *
     * @param {uint} maxLen
     * @return {Uint8Array} received data package
     */
    Channel.prototype.receive = function (maxLen) {
        throw new Error('NotImplemented');
    };

    /**
     *  Sends a datagram via this channel.
     *
     * @param {Uint8Array} src       - data package to be sent
     * @param {SocketAddress} target - remote address
     * @return {int} the number of bytes sent, -1 on error
     */
    Channel.prototype.send = function (src, target) {
        throw new Error('NotImplemented');
    };

    //-------- namespace --------
    ns.net.Channel = Channel;

})(StarTrek, MONKEY);
