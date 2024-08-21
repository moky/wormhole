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
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Porter;
import chat.dim.port.Ship;
import chat.dim.type.AddressPairObject;

/**
 *  Star Docker
 *  ~~~~~~~~~~~
 */
public abstract class StarPorter extends AddressPairObject implements Porter {

    private Dock dock;

    private WeakReference<Delegate> delegateRef;
    private WeakReference<Connection> connectionRef;

    // remaining data to be sent
    private Departure lastOutgo;
    private List<byte[]> lastFragments;

    protected StarPorter(SocketAddress remote, SocketAddress local) {
        super(remote, local);
        dock = createDock();
        delegateRef = null;
        connectionRef = null;
        // remaining data to be sent
        lastOutgo = null;
        lastFragments = new ArrayList<>();
    }

    @Override
    protected void finalize() throws Throwable {
        // make sure the relative connection is closed
        setConnection(null);
        dock = null;
        super.finalize();
    }

    // override for user-customized dock
    protected Dock createDock() {
        return new LockedDock();
    }

    // delegate for handling docker events
    public void setDelegate(Delegate keeper) {
        delegateRef = keeper == null ? null : new WeakReference<>(keeper);
    }
    protected Delegate getDelegate() {
        WeakReference<Delegate> ref = delegateRef;
        return ref == null ? null : ref.get();
    }

    //
    //  Connection
    //

    protected Connection getConnection() {
        WeakReference<Connection> ref = connectionRef;
        return ref == null ? null : ref.get();
    }
    protected void setConnection(Connection conn) {
        // 1. replace with new connection
        Connection old = getConnection();
        if (conn != null) {
            connectionRef = new WeakReference<>(conn);
        } else {
            connectionRef.clear();
            // connectionRef = null;
        }
        // 2. close old connection
        if (old != null && old != conn) {
            old.close();
        }
    }

    //
    //  Flags
    //

    @Override
    public boolean isOpen() {
        if (connectionRef == null) {
            // initializing
            return true;
        }
        Connection conn = getConnection();
        return conn == null || conn.isOpen();
    }

    @Override
    public boolean isAlive() {
        Connection conn = getConnection();
        return conn != null && conn.isAlive();
    }

    @Override
    public Status getStatus() {
        Connection conn = getConnection();
        return Status.getStatus(conn == null ? null : conn.getState());
    }

    /*/
    @Override
    public SocketAddress getLocalAddress() {
        Connection conn = getConnection();
        return conn == null ? localAddress : conn.getLocalAddress();
    }
    /*/

    @Override
    public String toString() {
        String cname = getClass().getName();
        return "<" + cname + " remote=\"" + getRemoteAddress() + "\" local=\"" + getLocalAddress() + "\">\n\t"
                + getConnection() + "\n</" + cname + ">";
    }

    @Override
    public boolean sendShip(Departure ship) {
        return dock.addDeparture(ship);
    }

    @Override
    public void processReceived(byte[] data) {
        // 1. get income ship from received data
        List<Arrival> ships = getArrivals(data);
        if (ships == null || ships.isEmpty()) {
            // waiting for more data
            return;
        }
        Delegate keeper = getDelegate();
        for (Arrival income : ships) {
            // 2. check income ship for response
            income = checkArrival(income);
            if (income == null) {
                // waiting for more fragment
                continue;
            }
            // 3. callback for processing income ship with completed data package
            if (keeper != null) {
                keeper.onPorterReceived(income, this);
            }
        }
    }

    /**
     *  Get income ships from received data
     *
     * @param data - received data
     * @return income ships carrying data package/fragments
     */
    protected abstract List<Arrival> getArrivals(byte[] data);

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
     */
    protected Departure checkResponse(Arrival income) {
        // check response for linked departure ship (same SN)
        Departure linked = dock.checkResponse(income);
        if (linked == null) {
            // linked departure task not found, or not finished yet
            return null;
        }
        // all fragments responded, task finished
        Delegate keeper = getDelegate();
        if (keeper != null) {
            keeper.onPorterSent(linked, this);
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
     *  Get outgo ship from waiting queue
     *
     * @param now - current time
     * @return next new or timeout task
     */
    protected Departure getNextDeparture(Date now) {
        return dock.getNextDeparture(now);
    }

    @Override
    public void purge(Date now) {
        dock.purge(now);
    }

    @Override
    public void close() {
        setConnection(null);
    }

    //
    //  Processor
    //

    @Override
    public boolean process() {
        //
        //  1. get connection which is ready for sending data
        //
        Connection conn = getConnection();
        if (conn == null) {
            // waiting for connection
            return false;
        } else if (!conn.isVacant()) {
            // connection is not ready for sending data
            return false;
        }
        //
        //  2. get data waiting to be sent out
        //
        Departure outgo = lastOutgo;
        List<byte[]> fragments = lastFragments;
        if (outgo != null && fragments.size() > 0) {
            // got remaining fragments from last outgo task
            lastOutgo = null;
            lastFragments = new ArrayList<>();
        } else {
            // get next outgo task
            Date now = new Date();
            outgo = getNextDeparture(now);
            if (outgo == null) {
                // nothing to do now, return false to let the thread have a rest
                return false;
            } else if (outgo.getStatus(now).equals(Ship.Status.FAILED)) {
                Delegate keeper = getDelegate();
                if (keeper != null) {
                    // callback for mission failed
                    IOException e = new SocketException("Request timeout");
                    keeper.onPorterFailed(new IOError(e), outgo, this);
                }
                // task timeout, return true to process next one
                return true;
            } else {
                // get fragments from outgo task
                fragments = outgo.getFragments();
                if (fragments == null || fragments.size() == 0) {
                    // all fragments of this task have been sent already
                    // return true to process next one
                    return true;
                }
            }
        }
        //
        //  3. process fragments of outgo task
        //
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
                throw new SocketException("only " + index + "/" + fragments.size() + " fragments sent.");
            } else {
                // task done
                Delegate keeper = getDelegate();
                if (outgo.isImportant()) {
                    // this task needs response,
                    // so we cannot call 'onPorterSent()' immediately
                    // until the remote responded
                } else if (keeper != null) {
                    keeper.onPorterSent(outgo, this);
                }
                return true;
            }
        } catch (IOException e) {
            // socket error, callback
            error = new IOError(e);
        }
        //
        //  4. remove sent fragments
        //
        for (; index > 0; --index) {
            fragments.remove(0);
        }
        // remove partially sent data of next fragment
        if (sent > 0) {
            byte[] next = fragments.remove(0);
            byte[] part = new byte[next.length - sent];
            System.arraycopy(next, sent, part, 0, next.length - sent);
            fragments.add(0, part);
        }
        //
        //  5. store remaining data
        //
        lastOutgo = outgo;
        lastFragments = fragments;
        //
        //  6. callback for error
        //
        Delegate keeper = getDelegate();
        if (keeper != null) {
            // keeper.onPorterFailed(error, outgo, this);
            keeper.onPorterError(error, outgo, this);
        }
        return false;
    }

}
