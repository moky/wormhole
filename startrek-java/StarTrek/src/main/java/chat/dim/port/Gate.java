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

import java.io.IOException;
import java.net.SocketAddress;

import chat.dim.net.ConnectionState;
import chat.dim.skywalker.Processor;

/**
 *  Star Gate
 *  ~~~~~~~~~
 */
public interface Gate extends Processor {

    /**
     *  Send data to the remote peer
     *
     * @param data        - outgoing data package
     * @param source      - local address
     * @param destination - remote address
     * @return false on error
     */
    boolean send(byte[] data, SocketAddress source, SocketAddress destination) throws IOException;

    /**
     *  Get gate status with direction
     *
     * @param remote - remote address
     * @param local  - local address
     * @return gate status
     */
    Status getStatus(SocketAddress remote, SocketAddress local);

    enum Status {

        ERROR    (-1),
        INIT      (0),
        PREPARING (1),
        READY     (2);

        public final int value;

        Status(int v) {
            value = v;
        }

        public static Status getStatus(ConnectionState state) {
            if (state == null) {
                return INIT;
            } else if (state.equals(ConnectionState.READY)
                    || state.equals(ConnectionState.EXPIRED)
                    || state.equals(ConnectionState.MAINTAINING)) {
                return READY;
            } else if (state.equals(ConnectionState.PREPARING)) {
                return PREPARING;
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
         * @param local     - local address
         * @param gate      - current gate
         */
        void onStatusChanged(Status oldStatus, Status newStatus, SocketAddress remote, SocketAddress local, Gate gate);

        /**
         *  Callback when new package received
         *
         * @param income      - data package container
         * @param source      - remote address
         * @param destination - local address
         * @param gate        - current gate
         */
        void onReceived(Arrival income, SocketAddress source, SocketAddress destination, Gate gate);

        /**
         *  Callback when package sent
         *
         * @param outgo       - package container
         * @param source      - local address
         * @param destination - remote address
         * @param gate        - current gate
         */
        void onSent(Departure outgo, SocketAddress source, SocketAddress destination, Gate gate);

        /**
         *  Callback when package sent failed
         *
         * @param error       - error message
         * @param outgo       - package container
         * @param source      - local address
         * @param destination - remote address
         * @param gate        - current gate
         */
        void onError(Error error, Departure outgo, SocketAddress source, SocketAddress destination, Gate gate);
    }
}
