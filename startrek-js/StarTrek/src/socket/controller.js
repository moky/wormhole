'use strict';
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

    st.socket.SocketReader = Interface(null, null);
    var SocketReader = st.socket.SocketReader;

    /**
     *  Read data from socket
     *
     * @param {uint} maxLen - max length of received data
     * @return {Uint8Array} received data
     */
    SocketReader.prototype.read = function (maxLen) {};

    /**
     *  Receive data via socket, and return remote address
     *
     * @param {uint} maxLen - max length of received data
     * @return {Pair<Uint8Array, SocketAddress>} data & remote address
     */
    SocketReader.prototype.receive = function (maxLen) {};


    st.socket.SocketWriter = Interface(null, null);
    var SocketWriter = st.socket.SocketWriter;

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


    /**
     *  Socket Channel Controller
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     *  Reader, Writer, ErrorChecker
     *
     * @param {BaseChannel} channel
     */
    st.socket.ChannelController = function (channel) {
        BaseObject.call(this);
        this.__channel = channel;
    };
    var ChannelController = st.socket.ChannelController

    Class(ChannelController, BaseObject, null, null);

    /**
     *  Get the channel
     *
     * @return {st.socket.BaseChannel|st.net.Channel}
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
