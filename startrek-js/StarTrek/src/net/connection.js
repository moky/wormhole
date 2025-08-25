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

//! require 'namespace.js'

    st.net.Connection = Interface(null, [Ticker]);
    var Connection = st.net.Connection;

    //
    //  Flags
    //

    Connection.prototype.isOpen = function () {};
    Connection.prototype.isBound = function () {};
    Connection.prototype.isConnected = function () {};

    // this.isOpen() && (this.isConnected() || this.isBound());
    Connection.prototype.isAlive = function () {};

    /**
     *  Ready for reading
     */
    Connection.prototype.isAvailable = function () {};  // isAlive

    /**
     *  Ready for writing
     */
    Connection.prototype.isVacant = function () {};  // isAlive

    Connection.prototype.getLocalAddress = function () {};
    Connection.prototype.getRemoteAddress = function () {};

    /**
     *  Get connection state
     *
     * @return {ConnectionState}
     */
    Connection.prototype.getState = function () {};

    /**
     *  Send data
     *
     * @param {Uint8Array} data - outgo data package
     * @return {int} count of bytes sent, -1 on error
     */
    Connection.prototype.sendData = function (data) {};

    /**
     *  Process received data
     *
     * @param {Uint8Array} data - received data
     */
    Connection.prototype.onReceivedData = function (data) {};

    /**
     *  Close the connection
     */
    Connection.prototype.close = function () {};


    /**
     *  Connection Delegate
     *  ~~~~~~~~~~~~~~~~~~~
     */
    st.net.ConnectionDelegate = Interface(null, null);
    var ConnectionDelegate = st.net.ConnectionDelegate;

    /**
     *  Called when connection state is changed
     *
     * @param {ConnectionState} previous - old state
     * @param {ConnectionState} current  - new state
     * @param {Connection} connection    - current connection
     */
    ConnectionDelegate.prototype.onConnectionStateChanged = function (previous, current, connection) {};

    /**
     *  Called when connection received data
     *
     * @param {Uint8Array} data       - received data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionReceived = function (data, connection) {};

    /**
     *  Called after data sent via the connection
     *
     * @param {uint} sent             - length of sent bytes
     * @param {Uint8Array} data       - outgo data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionSent = function (sent, data, connection) {};

    /**
     *  Called when failed to send data via the connection
     *
     * @param {Error} error           - error message
     * @param {Uint8Array} data       - outgo data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionFailed = function (error, data, connection) {};

    /**
     *  Called when connection (receiving) error
     *
     * @param {Error} error           - error message
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionError = function (error, connection) {};


    /**
     *  Connection with sent/received time
     */
    st.net.TimedConnection = Interface(null, null);
    var TimedConnection = st.net.TimedConnection;

    TimedConnection.EXPIRES = Duration.ofSeconds(16);

    /**
     *  Get last time to send data
     *
     * @return {Date}
     */
    TimedConnection.prototype.getLastSentTime = function () {};

    /**
     *  Get last time to receive data
     *
     * @return {Date}
     */
    TimedConnection.prototype.getLastReceivedTime = function () {};

    /**
     *  Check whether data sent recently
     *
     * @param {Date} now
     */
    TimedConnection.prototype.isSentRecently = function (now) {};

    /**
     *  Check whether data received recently
     *
     * @param {Date} now
     */
    TimedConnection.prototype.isReceivedRecently = function (now) {};

    /**
     *  Check whether data not received long time ago
     *
     * @param {Date} now
     */
    TimedConnection.prototype.isNotReceivedLongTimeAgo = function (now) {};
