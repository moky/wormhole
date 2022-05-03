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

    var Channel = function () {};
    sys.Interface(Channel, null);

    Channel.prototype.isOpen = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    // Channel.prototype.isBound = function () {
    //     ns.assert(false, 'implement me!');
    //     return false;
    // };

    Channel.prototype.isAlive = function () {
        // return this.isOpen() && (this.isConnected() || this.isBound());
        ns.assert(false, 'implement me!');
        return false;
    };

    Channel.prototype.close = function () {
        ns.assert(false, 'implement me!');
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
        ns.assert(false, 'implement me!');
        return null;
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
        ns.assert(false, 'implement me!');
        return 0;
    };


    /*================================================*\
    |*          Selectable Channel                    *|
    \*================================================*/

    // Channel.prototype.configureBlocking = function (block) {
    //     ns.assert(false, 'implement me!');
    //     return null;
    // };

    // Channel.prototype.isBlocking = function () {
    //     ns.assert(false, 'implement me!');
    //     return false;
    // };


    /*================================================*\
    |*          Network Channel                       *|
    \*================================================*/

    // Channel.prototype.bind = function (local) {
    //     ns.assert(false, 'implement me!');
    //     return null;
    // };

    // Channel.prototype.getLocalAddress = function () {
    //     ns.assert(false, 'implement me!');
    //     return null;
    // };


    /*================================================*\
    |*          Socket/Datagram Channel               *|
    \*================================================*/

    /**
     *  Check whether this channel's network socket is connected.
     *
     * @return {boolean}
     */
    Channel.prototype.isConnected = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Connect to remote address
     *
     * @param {SocketAddress} remote - remote address
     * @return {boolean} true on success
     */
    Channel.prototype.connect = function (remote) {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Get remote address to which this channel's socket is connected.
     *
     * @return {SocketAddress} remote address
     */
    Channel.prototype.getRemoteAddress = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    //-------- namespace --------
    ns.net.Channel = Channel;

    ns.net.registers('Channel');

})(StarTrek, MONKEY);
