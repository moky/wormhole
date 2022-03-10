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
     *  Send data
     *
     * @param data        - outgo data package
     * @param destination - remote address; can be null when it's connected
     * @return count of bytes sent, probably zero when it's non-blocking mode
     */
    int send(byte[] data, SocketAddress destination);

    /**
     *  Process received data
     *
     * @param data   - received data
     * @param remote - remote address
     * @param local  - local address
     */
    void received(byte[] data, SocketAddress remote, SocketAddress local);

    /**
     *  Close the connection
     */
    void close();

    /**
     *  Get state
     *
     * @return connection state
     */
    ConnectionState getState();

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
        void onStateChanged(ConnectionState previous, ConnectionState current, Connection connection);

        /**
         *  Called when connection received data
         *
         * @param data        - received data package
         * @param source      - remote address
         * @param destination - local address
         * @param connection  - current connection
         */
        void onReceived(byte[] data, SocketAddress source, SocketAddress destination, Connection connection);

        /**
         *  Called after data sent
         *
         * @param sent        - length of sent bytes
         * @param data        - outgo data package
         * @param source      - local address
         * @param destination - remote address
         * @param connection  - current connection
         */
        void onSent(int sent, byte[] data, SocketAddress source, SocketAddress destination, Connection connection);

        /**
         *  Called when connection error
         *
         * @param error       - error message
         * @param data        - outgo data package
         * @param source      - local address
         * @param destination - remote address
         * @param connection  - current connection
         */
        void onError(Throwable error, byte[] data, SocketAddress source, SocketAddress destination, Connection connection);
    }
}
