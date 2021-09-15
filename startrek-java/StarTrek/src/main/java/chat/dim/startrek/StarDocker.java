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
package chat.dim.startrek;

import java.io.IOException;
import java.net.SocketAddress;
import java.util.Date;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.port.Ship;

public abstract class StarDocker implements Docker {

    private final SocketAddress remoteAddress;
    private final SocketAddress localAddress;

    private final Dock dock;

    protected StarDocker(SocketAddress remote, SocketAddress local) {
        super();
        remoteAddress = remote;
        localAddress = local;
        dock = createDock();
    }

    @Override
    public SocketAddress getRemoteAddress() {
        return remoteAddress;
    }

    @Override
    public SocketAddress getLocalAddress() {
        return localAddress;
    }

    // override for user-customized dock
    protected Dock createDock() {
        return new LockedDock();
    }

    /**
     *  Get related connection which status is 'ready'
     *
     * @return related connection
     */
    protected abstract Connection getConnection();

    /**
     *  Get delegate for handling events
     *
     * @return gate delegate
     */
    protected abstract Ship.Delegate getDelegate();

    @Override
    public boolean process() {
        // 1. get connection which is ready for sending data
        Connection conn = getConnection();
        if (conn == null) {
            // connection not ready now
            return false;
        }
        long now = (new Date()).getTime();
        // 2. get outgo task
        Departure outgo = getNextDeparture(now);
        if (outgo == null) {
            // nothing to do now
            return false;
        }
        // 3. process outgo task
        Throwable error = null;
        if (outgo.isFailed(now)) {
            // outgo task expired, callback
            error = new Error("Response timeout");
        } else {
            try {
                if (!sendDeparture(outgo)) {
                    // failed to send outgo package, callback
                    error = new Error("Connection error");
                }
            } catch (IOException e) {
                //e.printStackTrace();
                error = e;
            }
        }
        // callback
        Ship.Delegate delegate = getDelegate();
        if (error != null && delegate != null) {
            delegate.onError(error, outgo, localAddress, remoteAddress, conn);
        }
        return true;
    }

    @Override
    public void processReceived(final byte[] data) {
        // 1. get income ship from received data
        Arrival income = getArrival(data);
        if (income == null) {
            // waiting for more data
            return;
        }
        // 2. check income ship for response
        income = checkArrival(income);
        if (income == null) {
            // waiting for more fragment
            return;
        }
        // 3. process income ship with completed data package
        Ship.Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onReceived(income, remoteAddress, localAddress, getConnection());
        }
    }

    /**
     *  Get income Ship from received data
     *
     * @param data - received data
     * @return income ship carrying data package/fragment
     */
    protected abstract Arrival getArrival(final byte[] data);

    /**
     *  Check income ship for responding
     *
     * @param income - income ship carrying data package/fragment/response
     * @return income ship carrying completed data package
     */
    protected abstract Arrival checkArrival(final Arrival income);

    /**
     *  Check and remove linked departure ship with same SN (and page index for fragment)
     *
     * @param income - income ship with SN
     * @return linked outgo ship
     */
    protected Departure checkResponse(final Arrival income) {
        // check response for linked departure ship (same SN)
        Departure linked = dock.checkResponse(income);
        if (linked == null) {
            // linked departure task not found
            return null;
        }
        // all fragments responded, task finished
        Ship.Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onSent(linked, localAddress, remoteAddress, getConnection());
        }
        return linked;
    }

    /**
     * Check received ship for completed package
     *
     * @param income - income ship carrying data package (fragment)
     * @return ship carrying completed data package
     */
    protected Arrival assembleArrival(final Arrival income) {
        return dock.assembleArrival(income);
    }

    /**
     *  Append outgo Ship to the waiting queue
     *
     * @param outgo - departure task
     * @return false on duplicated
     */
    protected boolean appendDeparture(final Departure outgo) {
        return dock.appendDeparture(outgo);
    }

    /**
     *  Get outgo Ship from waiting queue
     *
     * @param now - current time
     * @return next new or timeout task
     */
    protected Departure getNextDeparture(final long now) {
        // this will be remove from the queue,
        // if needs retry, the caller should append it back
        return dock.getNextDeparture(now);
    }

    /**
     *  Sending all fragments in the ship
     *
     * @param outgo - outgo ship carried package/fragments
     * @return true on sent
     */
    private boolean sendDeparture(final Departure outgo) throws IOException {
        List<byte[]> fragments = outgo.getFragments();
        if (fragments == null || fragments.size() == 0) {
            // all fragments sent
            return true;
        }
        Connection conn = getConnection();
        if (conn == null) {
            // connection not ready now
            return false;
        }
        int success = 0;
        for (byte[] pkg : fragments) {
            if (conn.send(pkg, remoteAddress) != -1) {
                success += 1;
            }
        }
        return success == fragments.size();
    }

    @Override
    public void purge() {
        dock.purge();
    }
}
