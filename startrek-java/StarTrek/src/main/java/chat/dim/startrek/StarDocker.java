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

import java.io.IOError;
import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.port.Ship;
import chat.dim.type.AddressPairObject;

public abstract class StarDocker extends AddressPairObject implements Docker {

    private final WeakReference<Connection> connectionRef;
    private WeakReference<Delegate> delegateRef;

    private Dock dock;

    // remaining data to be sent
    private Departure lastOutgo;
    private List<byte[]> lastFragments;

    protected StarDocker(Connection conn) {
        super(conn.getRemoteAddress(), conn.getLocalAddress());
        connectionRef = new WeakReference<>(conn);
        delegateRef = new WeakReference<>(null);
        dock = createDock();
        lastOutgo = null;
        lastFragments = new ArrayList<>();
    }

    @Override
    protected void finalize() throws Throwable {
        // make sure the relative connection is closed
        removeConnection();
        super.finalize();
    }

    // override for user-customized dock
    protected Dock createDock() {
        return new LockedDock();
    }

    // delegate for handling docker events
    public void setDelegate(Delegate delegate) {
        delegateRef = new WeakReference<>(delegate);
    }
    protected Delegate getDelegate() {
        return delegateRef.get();
    }

    protected Connection getConnection() {
        return connectionRef.get();
    }
    private void removeConnection() {
        // 1. clear connection reference
        Connection old = connectionRef.get();
        connectionRef.clear();
        // 2. close old connection
        if (old != null && old.isOpen()) {
            old.close();
        }
    }

    @Override
    public boolean isOpen() {
        Connection conn = getConnection();
        return conn != null && conn.isOpen();
    }

    @Override
    public boolean isAlive() {
        Connection conn = getConnection();
        return conn != null && conn.isAlive();
    }

    @Override
    public Status getStatus() {
        Connection conn = getConnection();
        return conn == null ? Status.ERROR : Status.getStatus(conn.getState());
    }

    /*/
    @Override
    public SocketAddress getLocalAddress() {
        Connection conn = getConnection();
        return conn == null ? localAddress : conn.getLocalAddress();
    }
    /*/

    @Override
    public boolean sendShip(Departure ship) {
        return dock.appendDeparture(ship);
    }

    @Override
    public void processReceived(byte[] data) {
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
        // 3. callback for processing income ship with completed data package
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onDockerReceived(income, this);
        }
    }

    /**
     *  Get income Ship from received data
     *
     * @param data - received data
     * @return income ship carrying data package/fragment
     */
    protected abstract Arrival getArrival(byte[] data);

    /**
     *  Check income ship for responding
     *
     * @param income - income ship carrying data package/fragment/response
     * @return income ship carrying completed data package
     */
    protected abstract Arrival checkArrival(Arrival income);

    /**
     *  Check and remove linked departure ship with same SN (and page index for fragment)
     *
     * @param income - income ship with SN
     * @return linked outgo ship
     */
    protected Departure checkResponse(Arrival income) {
        // check response for linked departure ship (same SN)
        Departure linked = dock.checkResponse(income);
        if (linked == null) {
            // linked departure task not found, or not finished yet
            return null;
        }
        // all fragments responded, task finished
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onDockerSent(linked, this);
        }
        return linked;
    }

    /**
     * Check received ship for completed package
     *
     * @param income - income ship carrying data package (fragment)
     * @return ship carrying completed data package
     */
    protected Arrival assembleArrival(Arrival income) {
        return dock.assembleArrival(income);
    }

    /**
     *  Get outgo Ship from waiting queue
     *
     * @param now - current time
     * @return next new or timeout task
     */
    protected Departure getNextDeparture(long now) {
        // this will be remove from the queue,
        // if needs retry, the caller should append it back
        return dock.getNextDeparture(now);
    }

    @Override
    public void purge() {
        dock.purge();
    }

    @Override
    public void close() {
        removeConnection();
        dock = null;
    }

    //
    //  Processor
    //

    @Override
    public boolean process() {
        // 1. get connection which is ready for sending data
        Connection conn = getConnection();
        if (conn == null || !conn.isAlive()) {
            // connection not ready now
            return false;
        }
        // 2. get data waiting to be sent out
        Departure outgo;
        List<byte[]> fragments;
        if (lastFragments.size() > 0) {
            // get remaining fragments from last outgo task
            outgo = lastOutgo;
            fragments = lastFragments;
            lastOutgo = null;
            lastFragments = new ArrayList<>();
        } else {
            // get next outgo task
            long now = System.currentTimeMillis();
            outgo = getNextDeparture(now);
            if (outgo == null) {
                // nothing to do now, return false to let the thread have a rest
                return false;
            } else if (outgo.getState(now).equals(Ship.State.FAILED)) {
                Delegate delegate = getDelegate();
                if (delegate != null) {
                    // callback for mission failed
                    IOException e = new SocketException("Request timeout");
                    delegate.onDockerFailed(new IOError(e), outgo, this);
                }
                // task timeout, return true to process next one
                return true;
            } else {
                // get fragments from outgo task
                fragments = outgo.getFragments();
                if (fragments.size() == 0) {
                    // all fragments of this task have been sent already
                    // return true to process next one
                    return true;
                }
            }
        }
        // 3. process fragments of outgo task
        IOError error;
        int index = 0, sent = 0;
        try {
            for (byte[] fra : fragments) {
                sent = conn.send(fra);
                if (sent < fra.length) {
                    // buffer overflow?
                    break;
                } else {
                    assert sent == fra.length : "length of fragment sent error: " + sent + ", " + fra.length;
                    index += 1;
                    sent = 0;  // clear counter
                }
            }
            if (index < fragments.size()) {
                // task failed
                throw  new SocketException("only " + index + "/" + fragments.size() + " fragments sent.");
            } else {
                // task done
                return true;
            }
        } catch (IOException e) {
            // socket error, callback
            error = new IOError(e);
        }
        // 4. remove sent fragments
        for (; index > 0; --index) {
            fragments.remove(0);
        }
        // remove partially sent data of next fragment
        if (sent > 0) {
            byte[] last = fragments.remove(0);
            byte[] part = new byte[last.length - sent];
            System.arraycopy(last, sent, part, 0, last.length - sent);
            fragments.add(0, part);
        }
        // 5. store remaining data
        lastOutgo = outgo;
        lastFragments = fragments;
        // 6. callback for error
        Delegate delegate = getDelegate();
        if (delegate != null) {
            //delegate.onDockerFailed(error, outgo, this);
            delegate.onDockerError(error, outgo, this);
        }
        return false;
    }
}
