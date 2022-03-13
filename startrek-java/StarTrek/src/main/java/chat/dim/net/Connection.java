/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * ==============================================================================
 */
package chat.dim.net;

import java.net.SocketAddress;

import chat.dim.threading.Ticker;

public interface Connection extends Ticker {

    //
    //  Flags
    //
    boolean isOpen();  // not closed
    boolean isBound();
    boolean isConnected();

    boolean isAlive();  // isOpen() && (isConnected() || isBound())

    SocketAddress getLocalAddress();
    SocketAddress getRemoteAddress();

    /**
     *  Get state
     *
     * @return connection state
     */
    ConnectionState getState();

    /**
     *  Send data
     *
     * @param data        - outgo data package
     * @return count of bytes sent, probably zero when it's non-blocking mode
     */
    int send(byte[] data);

    /**
     *  Process received data
     *
     * @param data   - received data
     */
    void onReceived(byte[] data);

    /**
     *  Close the connection
     */
    void close();

    /**
     *  Connection Delegate
     *  ~~~~~~~~~~~~~~~~~~~
     */
    interface Delegate {

        /**
         *  Called when connection state is changed
         *
         * @param previous   - old state
         * @param current    - new state
         * @param connection - current connection
         */
        void onConnectionStateChanged(ConnectionState previous, ConnectionState current, Connection connection);

        /**
         *  Called when connection received data
         *
         * @param data        - received data package
         * @param connection  - current connection
         */
        void onConnectionReceived(byte[] data, Connection connection);

        /**
         *  Called after data sent via the connection
         *
         * @param sent        - length of sent bytes
         * @param data        - outgo data package
         * @param connection  - current connection
         */
        void onConnectionSent(int sent, byte[] data, Connection connection);

        /**
         *  Called when failed to send data via the connection
         *
         * @param error       - error message
         * @param data        - outgo data package
         * @param connection  - current connection
         */
        void onConnectionFailed(Throwable error, byte[] data, Connection connection);

        /**
         *  Called when connection (receiving) error
         *
         * @param error       - error message
         * @param data        - outgo data package
         * @param connection  - current connection
         */
        void onConnectionError(Throwable error, byte[] data, Connection connection);
    }
}
