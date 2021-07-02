/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
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

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;

import chat.dim.threading.Ticker;

public interface Connection extends Ticker {

    //
    //  Flags
    //
    boolean isOpen();  // not closed
    boolean isBound();
    boolean isConnected();

    SocketAddress getLocalAddress();
    SocketAddress getRemoteAddress();

    /**
     *  Send data
     *
     * @param src    - outgo buffer
     * @param target - remote address; can be null when it's connected
     * @return count of bytes sent, probably zero when it's non-blocking mode
     */
    int send(ByteBuffer src, SocketAddress target) throws IOException;

    /**
     *  Receive data
     *
     * @param dst    - income buffer
     * @return remote address; null on received nothing
     */
    SocketAddress receive(ByteBuffer dst) throws IOException;

    /**
     *  Close the connection
     */
    void close();

    /**
     *  Get status
     *
     * @return connection status
     */
    ConnectionState getState();

    /**
     *  Connection Delegate
     *  ~~~~~~~~~~~~~~~~~~~
     */
    interface Delegate {

        /**
         *  Call when connection status changed
         *
         * @param connection - current connection
         * @param current    - old state
         * @param next       - new state
         */
        void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next);
    }
}
