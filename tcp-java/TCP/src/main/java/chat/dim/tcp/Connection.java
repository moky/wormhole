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
package chat.dim.tcp;

public interface Connection extends Runnable {

    /*  Max length of memory cache
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    int MAX_CACHE_LENGTH = 65536;  // 64 KB

    long EXPIRES = 16 * 1000;  // 16 seconds

    /**
     *  Send data package
     *
     * @param data - package
     * @return count of bytes sent, -1 on error
     */
    int send(byte[] data);

    /**
     *  Get received data count
     *
     * @return count of received data
     */
    int available();

    /**
     *  Get received data from cache, and remove it
     *  (call available() to check first)
     *
     * @param maxLength - how many bytes to receive
     * @return received data
     */
    byte[] receive(int maxLength);

    /**
     *  Get remote address
     *
     * @return IP
     */
    String getHost();
    int getPort();

    /**
     *  Close the connection
     */
    void stop();

    /**
     *  Check whether connection is still running
     *
     * @return true on running
     */
    boolean isRunning();

    /**
     *  Get status
     *
     * @return connection status
     */
    ConnectionState getState();

    interface Delegate {

        /**
         *  Call when connection status changed
         *
         * @param connection - current connection
         * @param oldStatus - status before
         * @param newStatus - status after
         */
        void onConnectionStateChanged(Connection connection, ConnectionState oldStatus, ConnectionState newStatus);
    }
}
