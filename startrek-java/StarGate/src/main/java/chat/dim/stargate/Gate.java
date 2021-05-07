/* license: https://mit-license.org
 *
 *  Star Gate: Interfaces for network connection
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
package chat.dim.stargate;

import chat.dim.tcp.Connection;

public interface Gate {

    /**
     *  Get callback
     *
     * @return gate delegate
     */
    Gate.Delegate getDelegate();

    /**
     *  Check whether StarGate is not closed and the current Connection is active
     *
     * @return false on error
     */
    boolean isOpened();

    /**
     *  Check whether Connection Status is expired for maintaining
     *
     * @return true on waiting for heartbeat
     */
    boolean isExpired();

    /**
     *  Send data package to the connected server
     *
     * @param payload  - request data
     * @param priority - priority, -1 is the most fast
     * @param delegate - callback
     */
    boolean send(byte[] payload, int priority, Ship.Delegate delegate);

    //
    //  Connection
    //

    /**
     *  Send data package
     *
     * @param pack - data package
     * @return false on error
     */
    boolean send(byte[] pack);

    /**
     *  Get received data from cache, but not remove
     *
     * @return received data
     */
    byte[] received();

    /**
     *  Get received data from cache, and remove it
     *  (call 'received()' to check data first)
     *
     * @param length - how many bytes to receive
     * @return received data
     */
    byte[] receive(int length);

    //
    //  Ship Docking
    //

    /**
     *  Park this outgo Ship in a waiting queue for departure
     *
     * @param outgo - outgo ship
     * @return False on duplicated
     */
    boolean parkShip(StarShip outgo);

    /**
     *  Pull out an outgo Ship from waiting queue
     *
     * @param sn - ship ID
     * @return outgo Ship
     */
    StarShip pullShip(byte[] sn);  // Get a Ship(with SN as ID) and remove it from the Dock
    StarShip pullShip();           // Get a new Ship(time == 0) and remove it from the Dock

    /**
     *  Get any Ship timeout/expired (keep it in the waiting queue)
     *
     * @return outgo Ship
     */
    StarShip anyShip();

    //
    //  Gate Status
    //

    /**
     *  Get connection status
     *
     * @return gate status
     */
    Status getStatus();

    //
    //  Connection Status -> Gate Status
    //
    static Status getStatus(Connection.Status status) {
        switch (status) {
            case Connecting:
                return Status.Connecting;
            case Connected:
            case Maintaining:
            case Expired:
                return Status.Connected;
            case Error:
                return Status.Error;
            default:
                return Status.Init;
        }
    }

    enum Status {

        Error     (-1),
        Init       (0),
        Connecting (1),
        Connected  (2);

        public final int value;

        Status(int v) {
            value = v;
        }
    }

    //
    //  Gate Delegate
    //

    interface Delegate {

        /**
         *  Callback when connection status changed
         *
         * @param gate      - remote gate
         * @param oldStatus - last status
         * @param newStatus - current status
         */
        void onStatusChanged(Gate gate, Gate.Status oldStatus, Gate.Status newStatus);

        /**
         *  Callback when new package received
         *
         * @param gate      - remote gate
         * @param ship      - data package container
         * @return response
         */
        byte[] onReceived(Gate gate, Ship ship);
    }

    class Error extends java.lang.Error {
        public final Ship ship;
        Error(Ship s, String message) {
            super(message);
            ship = s;
        }
    }
}
