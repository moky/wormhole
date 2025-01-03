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

import java.io.IOError;
import java.net.SocketAddress;
import java.util.Date;

import chat.dim.net.ConnectionState;
import chat.dim.skywalker.Processor;

/**
 *  Star Docker
 *  ~~~~~~~~~~~
 *
 *  Processor for Star Ships
 */
public interface Porter extends Processor {

    boolean isOpen();    // connection.isOpen()
    boolean isAlive();   // connection.isAlive()

    Status getStatus();  // connection.getState()

    SocketAddress getRemoteAddress();
    SocketAddress getLocalAddress();

    /**
     *  Pack data to an outgo ship (with normal priority), and
     *  append to the waiting queue for sending out
     *
     * @param payload  - data to be sent
     * @return false on error
     */
    boolean sendData(byte[] payload);

    /**
     *  Append outgo ship (carrying data package, with priority)
     *  to the waiting queue for sending out
     *
     * @param ship - outgo ship carrying data package/fragment
     * @return false on duplicated
     */
    boolean sendShip(Departure ship);

    /**
     *  Called when received data
     *
     * @param data   - received data package
     */
    void processReceived(byte[] data);

    /**
     *  Send 'PING' for keeping connection alive
     */
    void heartbeat();

    /**
     *  Clear all expired tasks
     */
    int purge(Date now);

    /**
     *  Close connection for this docker
     */
    void close();

    /**
     *  Docker Status
     *  ~~~~~~~~~~~~~
     */
    enum Status {

        INIT      (0),
        PREPARING (1),
        READY     (2),
        ERROR    (-1);

        public final int value;

        Status(int v) {
            value = v;
        }

        public static Status getStatus(ConnectionState state) {
            if (state == null) {
                return ERROR;
            } else if (state.equals(ConnectionState.Order.READY)
                    || state.equals(ConnectionState.Order.EXPIRED)
                    || state.equals(ConnectionState.Order.MAINTAINING)) {
                return READY;
            } else if (state.equals(ConnectionState.Order.PREPARING)) {
                return PREPARING;
            } else if (state.equals(ConnectionState.Order.ERROR)) {
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
    interface Delegate {

        /**
         *  Callback when new package received
         *
         * @param arrival     - income data package container
         * @param porter      - connection docker
         */
        void onPorterReceived(Arrival arrival, Porter porter);

        /**
         *  Callback when package sent
         *
         * @param departure   - outgo data package container
         * @param porter      - connection docker
         */
        void onPorterSent(Departure departure, Porter porter);

        /**
         *  Callback when failed to send package
         *
         * @param error       - error message
         * @param departure   - outgo data package container
         * @param porter      - connection docker
         */
        void onPorterFailed(IOError error, Departure departure, Porter porter);

        /**
         *  Callback when connection error
         *
         * @param error       - error message
         * @param departure   - outgo data package container
         * @param porter      - connection docker
         */
        void onPorterError(IOError error, Departure departure, Porter porter);

        /**
         *  Callback when connection status changed
         *
         * @param previous    - old status
         * @param current     - new status
         * @param porter      - connection docker
         */
        void onPorterStatusChanged(Status previous, Status current, Porter porter);

    }

}
