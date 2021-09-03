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
package chat.dim.port;

import java.net.SocketAddress;

import chat.dim.net.ConnectionState;

/**
 *  Star Gate
 *  ~~~~~~~~~
 */
public interface Gate {

    /**
     *  Send payload to the remote peer
     *
     * @param data   - outgoing data package
     * @param remote - remote address
     * @return false on error
     */
    boolean send(byte[] data, SocketAddress remote);

    /**
     *  Get gate status with direction
     *
     * @param remote - remote address
     * @return gate status
     */
    Status getStatus(SocketAddress remote);

    enum Status {

        ERROR     (-1),
        INIT       (0),
        CONNECTING (1),
        CONNECTED  (2);

        public final int value;

        Status(int v) {
            value = v;
        }

        public static Status getStatus(ConnectionState state) {
            if (state == null) {
                return INIT;
            } else if (state.equals(ConnectionState.CONNECTED)
                    || state.equals(ConnectionState.EXPIRED)
                    || state.equals(ConnectionState.MAINTAINING)) {
                return CONNECTED;
            } else if (state.equals(ConnectionState.CONNECTING)) {
                return CONNECTING;
            } else if (state.equals(ConnectionState.ERROR)) {
                return ERROR;
            } else {
                return INIT;
            }
        }
    }

    /**
     *  Gate Delegate
     *  ~~~~~~~~~~~~~
     */
    interface Delegate {

        /**
         *  Callback when connection status changed
         *
         * @param oldStatus - last status
         * @param newStatus - current status
         * @param remote    - remote address
         * @param gate      - current gate
         */
        void onStatusChanged(Status oldStatus, Status newStatus, SocketAddress remote, Gate gate);

        /**
         *  Callback when new package received
         *
         * @param ship      - data package container
         * @param remote    - remote address
         * @param gate      - current gate
         */
        void onReceived(Arrival ship, SocketAddress remote, Gate gate);

        /**
         *  Callback when package sent
         *
         * @param ship      - package container
         * @param remote    - remote address
         * @param gate      - current gate
         */
        void onSent(Departure ship, SocketAddress remote, Gate gate);

        /**
         *  Callback when package sent failed
         *
         * @param error     - error message
         * @param ship      - package container
         * @param remote    - remote address
         * @param gate      - current gate
         */
        void onError(Error error, Departure ship, SocketAddress remote, Gate gate);
    }
}
