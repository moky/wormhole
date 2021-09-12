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

/**
 *  Star Ship
 *  ~~~~~~~~~
 *
 *  Container carrying data package
 */
public interface Ship {

    /**
     *  Get ID for this Ship
     *
     * @return SN
     */
    Object getSN();

    /**
     *  Check whether task failed
     *
     * @param now - current time
     * @return true on failed
     */
    boolean isFailed(long now);

    /**
     *  Update expired time
     *
     * @param now - current time
     * @return false on error (nothing changed)
     */
    boolean update(long now);

    /**
     *  Ship Delegate
     *  ~~~~~~~~~~~~~
     */
    interface Delegate {

        /**
         *  Callback when new package received
         *
         * @param arrival     - income data package container
         * @param source      - remote address
         * @param destination - local address
         * @param connection  - current connection
         */
        void onReceived(Arrival arrival,
                        SocketAddress source, SocketAddress destination, Connection connection);

        /**
         *  Callback when package sent
         *
         * @param departure   - outgo data package container
         * @param source      - local address
         * @param destination - remote address
         * @param connection  - current connection
         */
        void onSent(Departure departure,
                    SocketAddress source, SocketAddress destination, Connection connection);

        /**
         *  Callback when package sent failed
         *
         * @param error       - error message
         * @param departure   - outgo data package container
         * @param source      - local address
         * @param destination - remote address
         * @param connection  - current connection
         */
        void onError(Throwable error, Departure departure,
                     SocketAddress source, SocketAddress destination, Connection connection);
    }
}
