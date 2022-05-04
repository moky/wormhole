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

    var ChannelChecker = function () {};
    sys.Interface(ChannelChecker, null);

    // 1. check E_AGAIN
    //    the socket will raise 'Resource temporarily unavailable'
    //    when received nothing in non-blocking mode,
    //    or buffer overflow while sending too many bytes,
    //    here we should ignore this exception.
    // 2. check timeout
    //    in blocking mode, the socket will wait until send/received data,
    //    but if timeout was set, it will raise 'timeout' error on timeout,
    //    here we should ignore this exception
    ChannelChecker.prototype.checkError = function (error, sock) {
        ns.assert(false, 'implement me!');
        return null;
    };

    // 1. check timeout
    //    in blocking mode, the socket will wait until received something,
    //    but if timeout was set, it will return nothing too, it's normal;
    //    otherwise, we know the connection was lost.
    ChannelChecker.prototype.checkData = function (buf, len, sock) {
        ns.assert(false, 'implement me!');
        return null;
    };

    //-------- namespace --------
    ns.socket.ChannelChecker = ChannelChecker;

    ns.socket.registers('ChannelChecker');

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var ChannelChecker = ns.socket.ChannelChecker;

    var DefaultChecker = function () {
        Object.call(this);
    };
    sys.Class(DefaultChecker, Object, [ChannelChecker], {
        // Override
        checkError: function (error, sock) {
            // TODO: check 'E_AGAIN' & TimeoutException
            return error;
        },
        // Override
        checkData: function (buf, len, sock) {
            // TODO: check Timeout for received nothing
            if (len === -1) {
                return new Error('channel closed');
            }
            return null;
        }
    })

    /**
     *  Socket Channel Controller
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     *  Reader, Writer, ErrorChecker
     *
     * @param {BaseChannel} channel
     */
    var ChannelController = function (channel) {
        Object.call(this);
        this.__channel = channel;
        this.__checker = this.createChecker();
    };
    sys.Class(ChannelController, Object, [ChannelChecker], null);

    /**
     *  Get the channel
     *
     * @return {BaseChannel|Channel}
     */
    ChannelController.prototype.getChannel = function () {
        return this.__channel;
    };

    /**
     *  Get remote address
     *
     * @return {SocketAddress}
     */
    ChannelController.prototype.getRemoteAddress = function () {
        var channel = this.getChannel();
        return channel.getRemoteAddress();
    };

    /**
     *  Get local address
     *
     * @return {SocketAddress}
     */
    ChannelController.prototype.getLocalAddress = function () {
        var channel = this.getChannel();
        return channel.getLocalAddress();
    };

    /**
     *  Get inner socket
     *
     * @return {*}
     */
    ChannelController.prototype.getSocket = function () {
        var channel = this.getChannel();
        return channel.getSocketChannel();
    };

    //
    //  Checker
    //
    ChannelController.prototype.createChecker = function () {
        return new DefaultChecker();
    };

    // Override
    ChannelController.prototype.checkError = function (error, sock) {
        return this.__checker.checkError(error, sock);
    };

    // Override
    ChannelController.prototype.checkData = function (buf, len, sock) {
        return this.__checker.checkData(buf, len, sock);
    };

    //-------- namespace --------
    ns.socket.ChannelController = ChannelController;

    ns.socket.registers('ChannelController');

})(StarTrek, MONKEY);
