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

public interface Connection {

    long EXPIRES = 16 * 1000;  // 16 seconds

    /**
     *  Send data package
     *
     * @param data - package
     * @return -1 on error
     */
    int send(byte[] data);

    /**
     *  Get received data from cache, but not remove
     *
     * @return received data
     */
    byte[] received();

    /**
     *  Get received data from cache, and remove it
     *  (call received() to check data first)
     *
     * @param length - how many bytes to receive
     * @return received data
     */
    byte[] receive(int length);

    /**
     *  Get status
     *
     * @return connection status
     */
    Status getStatus();

    /*
     *  @enum ConnectionStatus
     *
     *  @abstract Defined for indicating connection status
     *
     *  @discussion connection status.
     *
     *      Default     - 'initialized', or sent timeout
     *      Connecting  - sent 'PING', waiting for response
     *      Connected   - got response recently
     *      Expired     - long time, needs maintaining (still connected)
     *      Maintaining - sent 'PING', waiting for response
     *      Error       - long long time no response, connection lost
     *
     *  Bits:
     *      0000 0001 - indicates sent something just now
     *      0000 0010 - indicates sent something not too long ago
     *
     *      0001 0000 - indicates received something just now
     *      0010 0000 - indicates received something not too long ago
     *
     *      (All above are just some advices to help choosing numbers :P)
     */
    enum Status {

        Default     (0x00),  // 0000 0000
        Connecting  (0x01),  // 0000 0001, sent just now
        Connected   (0x11),  // 0001 0001, received just now
        Maintaining (0x21),  // 0010 0001, received not long ago, sent just now
        Expired     (0x22),  // 0010 0010, received not long ago, needs sending
        Error       (0x88);  // 1000 1000, long time no response

        public final int value;

        Status(int value) {
            this.value = value;
        }
    }

    /*
     *    Finite States:
     *
     *             //===============\\          (Sent)          //==============\\
     *             ||               || -----------------------> ||              ||
     *             ||    Default    ||                          ||  Connecting  ||
     *             || (Not Connect) || <----------------------- ||              ||
     *             \\===============//         (Timeout)        \\==============//
     *                                                               |       |
     *             //===============\\                               |       |
     *             ||               || <-----------------------------+       |
     *             ||     Error     ||          (Error)                 (Received)
     *             ||               || <-----------------------------+       |
     *             \\===============//                               |       |
     *                 A       A                                     |       |
     *                 |       |            //===========\\          |       |
     *                 (Error) +----------- ||           ||          |       |
     *                 |                    ||  Expired  || <--------+       |
     *                 |       +----------> ||           ||          |       |
     *                 |       |            \\===========//          |       |
     *                 |       (Timeout)           |         (Timeout)       |
     *                 |       |                   |                 |       V
     *             //===============\\     (Sent)  |            //==============\\
     *             ||               || <-----------+            ||              ||
     *             ||  Maintaining  ||                          ||  Connected   ||
     *             ||               || -----------------------> ||              ||
     *             \\===============//       (Received)         \\==============//
     */

    interface Delegate {

        /**
         *  Call when connection status changed
         *
         * @param connection - current connection
         * @param oldStatus - status before
         * @param newStatus - status after
         */
        void onConnectionStatusChanged(Connection connection, Status oldStatus, Status newStatus);

        /**
         *  Call when received data from a connection
         *  (if data processed, must call 'connection.receive(data.length)' to remove it from cache pool)
         *
         * @param connection - current connection
         * @param data - received data
         */
        void onConnectionReceivedData(Connection connection, byte[] data);

        /**
         *  Call when connection's cache is full
         *
         * @param connection - current connection
         * @param ejected - dropped data
         */
        void onConnectionOverflowed(Connection connection, byte[] ejected);
    }
}
