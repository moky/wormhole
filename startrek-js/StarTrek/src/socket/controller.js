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
    SocketReader.prototype.read = function (maxLen) {};

    /**
     *  Receive data from socket
     *
     * @param {uint} maxLen - max length of received data
     * @return {Uint8Array} received data
     */
    SocketReader.prototype.receive = function (maxLen) {};

    var SocketWriter = Interface(null, null);

    /**
     *  Write data into socket
     *
     * @param {Uint8Array} src - data to be wrote
     * @return {int} -1 on error
     */
    SocketWriter.prototype.write = function (src) {};

    /**
     *  Send data via socket with remote address
     *
     * @param {Uint8Array} src       - data to send
     * @param {SocketAddress} target - remote address
     * @return {int} sent length, -1 on error
     */
    SocketWriter.prototype.send = function (src, target) {};

    //-------- namespace --------
    ns.socket.SocketReader = SocketReader;
    ns.socket.SocketWriter = SocketWriter;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Class        = sys.type.Class;
    var SocketHelper = ns.net.SocketHelper;

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
    };
    Class(ChannelController, Object, null, null);

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
        return !channel ? null : channel.getRemoteAddress();
    };

    /**
     *  Get local address
     *
     * @return {SocketAddress}
     */
    ChannelController.prototype.getLocalAddress = function () {
        var channel = this.getChannel();
        return !channel ? null : channel.getLocalAddress();
    };

    /**
     *  Get inner socket
     *
     * @return {WebSocket|*} WebSocket wrapper
     */
    ChannelController.prototype.getSocket = function () {
        var channel = this.getChannel();
        return !channel ? null : channel.getSocket();
    };

    // protected
    ChannelController.prototype.receivePackage = function (sock, maxLen) {
        // TODO: override for async receiving
        return SocketHelper.socketReceive(sock, maxLen);
    };

    // Override
    ChannelController.prototype.sendAll = function (sock, data) {
        // TODO: override for async sending
        return SocketHelper.socketSend(sock, data);
        // var sent = 0;
        // var rest = data.length;
        // var cnt;
        // while (sock.isOpen()) {
        //     cnt = sock.write(data);
        //     // check send result
        //     if (cnt <= 0) {
        //         // buffer overflow?
        //         break;
        //     }
        //     // something sent, check remaining data
        //     sent += cnt;
        //     rest -= cnt;
        //     if (rest <= 0) {
        //         // done!
        //         break;
        //     } else {
        //         // remove sent part
        //         data = data.subarray(cnt);
        //     }
        // }
        // return sent;
    };

    //-------- namespace --------
    ns.socket.ChannelController = ChannelController;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var SocketReader      = ns.socket.SocketReader;
    var SocketWriter      = ns.socket.SocketWriter;
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
            if (sock && sock.isOpen()) {
                return this.receivePackage(sock, maxLen);
            } else {
                throw new Error('channel closed');
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
            if (sock && sock.isOpen()) {
                return this.sendAll(sock, data)
            } else {
                throw new Error('channel closed');
            }
        }
    });

    //-------- namespace --------
    ns.socket.ChannelReader = ChannelReader;
    ns.socket.ChannelWriter = ChannelWriter;

})(StarTrek, MONKEY);
