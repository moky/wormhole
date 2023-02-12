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

(function (ns, fsm, sys) {
    'use strict';

    var Interface = sys.type.Interface;
    var Ticker = fsm.threading.Ticker;

    var Connection = Interface(null, [Ticker]);

    //
    //  Flags
    //

    Connection.prototype.isOpen = function () {
        throw new Error('NotImplemented');
    };

    Connection.prototype.isBound = function () {
        throw new Error('NotImplemented');
    };

    Connection.prototype.isConnected = function () {
        throw new Error('NotImplemented');
    };

    Connection.prototype.isAlive = function () {
        // return this.isOpen() && (this.isConnected() || this.isBound());
        throw new Error('NotImplemented');
    };

    Connection.prototype.getLocalAddress = function () {
        throw new Error('NotImplemented');
    };

    Connection.prototype.getRemoteAddress = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Get connection state
     *
     * @return {ConnectionState}
     */
    Connection.prototype.getState = function () {
        throw new Error('NotImplemented');
    };

    /**
     *  Send data
     *
     * @param {Uint8Array} data - outgo data package
     * @return {int} count of bytes sent, -1 on error
     */
    Connection.prototype.send = function (data) {
        throw new Error('NotImplemented');
    };

    /**
     *  Process received data
     *
     * @param {Uint8Array} data - received data
     */
    Connection.prototype.onReceived = function (data) {
        throw new Error('NotImplemented');
    };

    /**
     *  Close the connection
     */
    Connection.prototype.close = function () {
        throw new Error('NotImplemented');
    };

    //-------- namespace --------
    ns.net.Connection = Connection;

})(StarTrek, FiniteStateMachine, MONKEY);

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;

    /**
     *  Connection Delegate
     *  ~~~~~~~~~~~~~~~~~~~
     */
    var ConnectionDelegate = Interface(null, null);

    /**
     *  Called when connection state is changed
     *
     * @param {ConnectionState} previous - old state
     * @param {ConnectionState} current  - new state
     * @param {Connection} connection    - current connection
     */
    ConnectionDelegate.prototype.onConnectionStateChanged = function (previous, current, connection) {
        throw new Error('NotImplemented');
    };

    /**
     *  Called when connection received data
     *
     * @param {Uint8Array} data       - received data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionReceived = function (data, connection) {
        throw new Error('NotImplemented');
    };

    /**
     *  Called after data sent via the connection
     *
     * @param {uint} sent             - length of sent bytes
     * @param {Uint8Array} data       - outgo data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionSent = function (sent, data, connection) {
        throw new Error('NotImplemented');
    };

    /**
     *  Called when failed to send data via the connection
     *
     * @param {Error} error           - error message
     * @param {Uint8Array} data       - outgo data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionFailed = function (error, data, connection) {
        throw new Error('NotImplemented');
    };

    /**
     *  Called when connection (receiving) error
     *
     * @param {Error} error           - error message
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionError = function (error, connection) {
        throw new Error('NotImplemented');
    };

    //-------- namespace --------
    ns.net.ConnectionDelegate = ConnectionDelegate;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;

    var TimedConnection = Interface(null, null);

    TimedConnection.prototype.getLastSentTime = function () {
        throw new Error('NotImplemented');
    };

    TimedConnection.prototype.getLastReceivedTime = function () {
        throw new Error('NotImplemented');
    };

    TimedConnection.prototype.isSentRecently = function () {
        throw new Error('NotImplemented');
    };

    TimedConnection.prototype.isReceivedRecently = function () {
        throw new Error('NotImplemented');
    };

    TimedConnection.prototype.isNotReceivedLongTimeAgo = function () {
        throw new Error('NotImplemented');
    };

    //-------- namespace --------
    ns.net.TimedConnection = TimedConnection;

})(StarTrek, MONKEY);
