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

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.skywalker.Processor;

/**
 *  Star Worker
 *  ~~~~~~~~~~~
 *
 *  Processor for Star Ships
 */
public interface Docker extends Processor {

    boolean isAlive();  // connection.isAlive()

    SocketAddress getLocalAddress();
    SocketAddress getRemoteAddress();
    Connection getConnection();

    /**
     *  Called when received data
     *
     * @param data   - received data package
     */
    void processReceived(byte[] data);

    /**
     *  Append outgo ship to a queue for sending out
     *
     * @param outgo - outgo ship carrying data package/fragment
     * @return false on duplicated
     */
    boolean appendDeparture(Departure outgo);

    /**
     *  Pack the payload to an outgo Ship
     *
     * @param payload     - request data
     * @param priority    - smaller is faster (-1 is the most fast)
     * @param delegate    - callback handler for the departure ship
     * @return departure ship containing payload
     */
    Departure pack(byte[] payload, int priority, Ship.Delegate delegate);

    /**
     *  Send 'PING' for keeping connection alive
     */
    void heartbeat();

    /**
     *  Clear all expired tasks
     */
    void purge();

    /**
     *  Close connection for this docker
     */
    void close();

    /**
     *  Get docker status
     *
     * @return docker status
     */
    Status getStatus();

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
                return ERROR;
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
     *  Docker Delegate
     *  ~~~~~~~~~~~~~~~
     */
    interface Delegate extends Ship.Delegate {

        /**
         *  Callback when connection status changed
         *
         * @param previous    - old status
         * @param current     - new status
         * @param remote      - remote address
         * @param local       - local address
         * @param conn        - current connection
         * @param docker      - current docker
         */
        void onStatusChanged(Status previous, Status current,
                             SocketAddress remote, SocketAddress local, Connection conn,
                             Docker docker);
    }
}
