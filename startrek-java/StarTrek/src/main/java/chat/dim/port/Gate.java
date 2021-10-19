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

/*
 *  Architecture:
 *
 *                 Gate (Ship)       Gate (Ship)     Gate (Ship)
 *                 Delegate          Delegate        Delegate
 *                     ^                 ^               ^
 *                     :                 :               :
 *        ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
 *                     :                 :               :
 *          +==========V=================V===============V==========+
 *          ||         :                 :               :         ||
 *          ||         :      Gate       :               :         ||
 *          ||         :                 :               :         ||
 *          ||  +------------+    +------------+   +------------+  ||
 *          ||  |   docker   |    |   docker   |   |   docker   |  ||
 *          +===+------------+====+------------+===+------------+===+
 *          ||  | connection |    | connection |   | connection |  ||
 *          ||  +------------+    +------------+   +------------+  ||
 *          ||          :                :               :         ||
 *          ||          :      HUB       :...............:         ||
 *          ||          :                        :                 ||
 *          ||     +-----------+           +-----------+           ||
 *          ||     |  channel  |           |  channel  |           ||
 *          +======+-----------+===========+-----------+============+
 *                 |  socket   |           |  socket   |
 *                 +-----^-----+           +-----^-----+
 *                       : (TCP)                 : (UDP)
 *                       :               ........:........
 *                       :               :               :
 *        ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
 *                       :               :               :
 *                       V               V               V
 *                  Remote Peer     Remote Peer     Remote Peer
 */

import java.net.SocketAddress;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.skywalker.Processor;

/**
 *  Star Gate
 *  ~~~~~~~~~
 */
public interface Gate extends Processor {

    /**
     *  Get connection with direction
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on failed
     */
    Connection getConnection(SocketAddress remote, SocketAddress local);

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

    Delegate getDelegate();

    /**
     *  Gate Delegate
     *  ~~~~~~~~~~~~~
     */
    interface Delegate extends Ship.Delegate {

        /**
         *  Callback when connection status changed
         *
         * @param oldStatus   - last status
         * @param newStatus   - current status
         * @param remote      - remote address
         * @param local       - local address
         * @param gate        - current gate
         */
        void onStatusChanged(Status oldStatus, Status newStatus,
                             SocketAddress remote, SocketAddress local, Gate gate);
    }
}
