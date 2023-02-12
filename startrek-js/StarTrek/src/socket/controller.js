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

//! require 'channel.js'

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;
    var Class = sys.type.Class;

    var ChannelChecker = Interface(null, null);

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
        throw new Error('NotImplemented');
    };

    // 1. check timeout
    //    in blocking mode, the socket will wait until received something,
    //    but if timeout was set, it will return nothing too, it's normal;
    //    otherwise, we know the connection was lost.
    ChannelChecker.prototype.checkData = function (data, sock) {
        throw new Error('NotImplemented');
    };

    var DefaultChecker = function () {
        Object.call(this);
    };
    Class(DefaultChecker, Object, [ChannelChecker], {
        // Override
        checkError: function (error, sock) {
            // TODO: check 'E_AGAIN' & TimeoutException
            return error;
        },
        // Override
        checkData: function (data, sock) {
            // TODO: check Timeout for received nothing
            // if (!data) {
            //     return new Error('channel closed');
            // }
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
    Class(ChannelController, Object, [ChannelChecker], null);

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
     * @return {WebSocket|*} WebSocket wrapper
     */
    ChannelController.prototype.getSocket = function () {
        var channel = this.getChannel();
        return channel.getSocket();
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
    ChannelController.prototype.checkData = function (data, sock) {
        return this.__checker.checkData(data, sock);
    };

    //-------- namespace --------
    ns.socket.ChannelController = ChannelController;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var SocketReader = ns.socket.SocketReader;
    var SocketWriter = ns.socket.SocketWriter;
    var ChannelController = ns.socket.ChannelController;

    /**
     *  Channel Reader
     *  ~~~~~~~~~~~~~~
     *
     * @param {BaseChannel} channel
     */
    var ChannelReader = function (channel) {
        ChannelController.call(this, channel)
    };
    Class(ChannelReader, ChannelController, [SocketReader], {
        // Override
        read: function (maxLen) {
            var sock = this.getSocket();
            var data = this.tryRead(maxLen, sock);
            // check data
            var error = this.checkData(data, sock);
            if (error) {
                // connection lost
                throw error;
            }
            // OK
            return data;
        },
        // protected
        tryRead: function (maxLen, sock) {
            try {
                return sock.read(maxLen);
            } catch (e) {
                e = this.checkError(e, sock);
                if (e) {
                    // connection lost?
                    throw e;
                }
                // received nothing
                return null;
            }
        }
    });

    /**
     *  Channel Writer
     *  ~~~~~~~~~~~~~~
     *
     * @param {BaseChannel} channel
     */
    var ChannelWriter = function (channel) {
        ChannelController.call(this, channel)
    };
    Class(ChannelWriter, ChannelController, [SocketWriter], {
        // Override
        write: function (data) {
            var sock = this.getSocket();
            var sent = 0;
            var rest = data.length;
            var cnt;
            while (true) {  // while (sock.isOpen())
                cnt = this.tryWrite(data, sock);
                // check send result
                if (cnt <= 0) {
                    // buffer overflow?
                    break;
                }
                // something sent, check remaining data
                sent += cnt;
                rest -= cnt;
                if (rest <= 0) {
                    // done!
                    break;
                } else {
                    // remove sent part
                    data = data.subarray(cnt);
                }
            }
        },
        // protected
        tryWrite: function (data, sock) {
            try {
                return sock.write(data);
            } catch (e) {
                e = this.checkError(e, sock);
                if (e) {
                    // connection lost?
                    throw e;
                }
                // buffer overflow!
                return 0;
            }
        }
    });

    //-------- namespace --------
    ns.socket.ChannelReader = ChannelReader;
    ns.socket.ChannelWriter = ChannelWriter;

})(StarTrek, MONKEY);
