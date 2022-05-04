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

    var Ticker = sys.threading.Ticker;

    var Connection = function () {};
    sys.Interface(Connection, [Ticker]);

    //
    //  Flags
    //

    Connection.prototype.isOpen = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    Connection.prototype.isBound = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    Connection.prototype.isConnected = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    Connection.prototype.isAlive = function () {
        // return this.isOpen() && (this.isConnected() || this.isBound());
        ns.assert(false, 'implement me!');
        return false;
    };

    Connection.prototype.getLocalAddress = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    Connection.prototype.getRemoteAddress = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    /**
     *  Get connection state
     *
     * @return {ConnectionState}
     */
    Connection.prototype.getState = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    /**
     *  Send data
     *
     * @param {Uint8Array} data - outgo data package
     * @return {int} count of bytes sent, -1 on error
     */
    Connection.prototype.send = function (data) {
        ns.assert(false, 'implement me!');
        return 0;
    };

    /**
     *  Process received data
     *
     * @param {Uint8Array} data - received data
     */
    Connection.prototype.onReceived = function (data) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Close the connection
     */
    Connection.prototype.close = function () {
        ns.assert(false, 'implement me!');
    };

    //-------- namespace --------
    ns.net.Connection = Connection;

    ns.net.registers('Connection');

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    /**
     *  Connection Delegate
     *  ~~~~~~~~~~~~~~~~~~~
     */
    var ConnectionDelegate = function () {};
    sys.Interface(ConnectionDelegate, null);

    /**
     *  Called when connection state is changed
     *
     * @param {ConnectionState} previous - old state
     * @param {ConnectionState} current  - new state
     * @param {Connection} connection    - current connection
     */
    ConnectionDelegate.prototype.onConnectionStateChanged = function (previous, current, connection) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Called when connection received data
     *
     * @param {Uint8Array} data       - received data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionReceived = function (data, connection) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Called after data sent via the connection
     *
     * @param {uint} sent             - length of sent bytes
     * @param {Uint8Array} data       - outgo data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionSent = function (sent, data, connection) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Called when failed to send data via the connection
     *
     * @param {Error} error           - error message
     * @param {Uint8Array} data       - outgo data package
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionFailed = function (error, data, connection) {
        ns.assert(false, 'implement me!');
    };

    /**
     *  Called when connection (receiving) error
     *
     * @param {Error} error           - error message
     * @param {Connection} connection - current connection
     */
    ConnectionDelegate.prototype.onConnectionError = function (error, connection) {
        ns.assert(false, 'implement me!');
    };

    //-------- namespace --------
    ns.net.ConnectionDelegate = ConnectionDelegate;

    ns.net.registers('ConnectionDelegate');

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var TimedConnection = function () {};
    sys.Interface(TimedConnection, null);

    TimedConnection.prototype.getLastSentTime = function () {
        ns.assert(false, 'implement me!');
        return 0;
    };

    TimedConnection.prototype.getLastReceivedTime = function () {
        ns.assert(false, 'implement me!');
        return 0;
    };

    TimedConnection.prototype.isSentRecently = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    TimedConnection.prototype.isReceivedRecently = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    TimedConnection.prototype.isNotReceivedLongTimeAgo = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    //-------- namespace --------
    ns.net.TimedConnection = TimedConnection;

    ns.net.registers('TimedConnection');

})(StarTrek, MONKEY);
