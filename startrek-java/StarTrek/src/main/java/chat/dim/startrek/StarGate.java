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
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.Date;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.port.Porter;
import chat.dim.type.AddressPairMap;

class PorterPool extends AddressPairMap<Porter> {

    @Override
    public Porter set(SocketAddress remote, SocketAddress local, Porter value) {
        // remove cached item
        Porter cached = super.remove(remote, local, value);
        /*/
        if (cached != null && cached != value) {
            cached.close();
        }
        /*/
        Porter old = super.set(remote, local, value);
        assert old != null : "should not happen";
        return cached;
    }

    /*/
    @Override
    public Porter remove(SocketAddress remote, SocketAddress local, Porter value) {
        Porter cached = super.remove(remote, local, value);
        if (cached != null && cached != value) {
            cached.close();
        }
        if (value != null) {
            value.close();
        }
        return cached;
    }
    /*/

}

public abstract class StarGate implements Gate, Connection.Delegate {

    private final WeakReference<Porter.Delegate> delegateRef;
    private final AddressPairMap<Porter> porterPool;
    private final ReadWriteLock lock;

    protected StarGate(Porter.Delegate keeper) {
        super();
        delegateRef = new WeakReference<>(keeper);
        porterPool = createPorterPool();
        lock = new ReentrantReadWriteLock();
    }

    protected AddressPairMap<Porter> createPorterPool() {
        return new PorterPool();
    }

    // delegate for handling docker events
    protected Porter.Delegate getDelegate() {
        return delegateRef.get();
    }

    @Override
    public boolean sendData(byte[] payload, SocketAddress remote, SocketAddress local) {
        Porter docker = getPorter(remote, local);
        if (docker == null) {
            assert false : "docker not found: " + local + " -> " + remote;
            return false;
        } else if (!docker.isAlive()) {
            assert false : "docker not alive: " + local + " -> " + remote;
            return false;
        }
        return docker.sendData(payload);
    }

    @Override
    public boolean sendShip(Departure outgo, SocketAddress remote, SocketAddress local) {
        Porter docker = getPorter(remote, local);
        if (docker == null) {
            assert false : "docker not found: " + local + " -> " + remote;
            return false;
        } else if (!docker.isAlive()) {
            assert false : "docker not alive: " + local + " -> " + remote;
            return false;
        }
        return docker.sendShip(outgo);
    }

    //
    //  Docker
    //

    /**
     *  Create new docker for received data
     *
     * @param remote - remote address
     * @param local  - local address
     * @return docker
     */
    protected abstract Porter createPorter(SocketAddress remote, SocketAddress local);

    protected Iterable<Porter> allPorters() {
        return porterPool.allValues();
    }

    protected Porter getPorter(SocketAddress remote, SocketAddress local) {
        return porterPool.get(remote, local);
    }

    protected Porter setPorter(SocketAddress remote, SocketAddress local, Porter porter) {
        return porterPool.set(remote, local, porter);
    }

    protected Porter removePorter(SocketAddress remote, SocketAddress local, Porter porter) {
        return porterPool.remove(remote, local, porter);
    }

    protected Porter dock(Connection conn, boolean newPorter) {
        //
        //  0. pre-checking
        //
        SocketAddress remote = conn.getRemoteAddress();
        SocketAddress local = conn.getLocalAddress();
        if (remote == null) {
            assert false : "remote address should not empty";
            return null;
        }
        Porter docker = getPorter(remote, local);
        if (docker != null) {
            return docker;
        }
        //
        //  1. lock to check
        //
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            // check again
            docker = getPorter(remote, local);
            if (docker != null || !newPorter) {
                return docker;
            }
            // docker not exists, create new docker
            docker = createPorter(remote, local);
            Porter cached = setPorter(remote, local, docker);
            if (cached != null && cached != docker) {
                cached.close();
            }
        } finally {
            writeLock.unlock();
        }
        //
        //  2. set connection for this docker
        //
        if (docker instanceof StarPorter) {
            ((StarPorter) docker).setConnection(conn);
        } else {
            assert false : "docker error: " + remote + ", " + docker;
        }
        return docker;
    }

    //
    //  Processor
    //

    @Override
    public boolean process() {
        Iterable<Porter> dockers = allPorters();
        // 1. drive all dockers to process
        int count = drivePorters(dockers);
        // 2. cleanup for dockers
        cleanupPorters(dockers);
        return count > 0;
    }
    protected int drivePorters(Iterable<Porter> porters) {
        int count = 0;
        for (Porter docker : porters) {
            if (docker.process()) {
                ++count;  // it's busy
            }
        }
        return count;
    }
    protected void cleanupPorters(Iterable<Porter> porters) {
        Date now = new Date();
        Porter cached;
        for (Porter docker : porters) {
            if (docker.isOpen()) {
                // clear expired tasks
                docker.purge(now);
            } else {
                // remove docker when connection closed
                cached = removePorter(docker.getRemoteAddress(), docker.getLocalAddress(), docker);
                if (cached != null && cached != docker) {
                    cached.close();
                }
            }
        }
    }

    /**
     *  Send a heartbeat package('PING') to remote address
     */
    protected void heartbeat(Connection connection) {
        SocketAddress remote = connection.getRemoteAddress();
        SocketAddress local = connection.getLocalAddress();
        Porter docker = getPorter(remote, local);
        if (docker != null) {
            docker.heartbeat();
        }
    }

    //
    //  Connection Delegate
    //

    @Override
    public void onConnectionStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        // convert status
        Porter.Status s1 = Porter.Status.getStatus(previous);
        Porter.Status s2 = Porter.Status.getStatus(current);
        // 1. callback when status changed
        boolean changed;
        if (s1 == null) {
            changed = s2 != null;
        } else if (s2 == null) {
            changed = true;
        } else {
            changed = !s1.equals(s2);
        }
        if (changed) {
            boolean finished = s2 != null && s2.equals(Porter.Status.ERROR);
            Porter docker = dock(connection, !finished);
            if (docker == null) {
                // connection closed and docker removed
                return;
            }
            // callback for docker status
            Porter.Delegate keeper = getDelegate();
            if (keeper != null) {
                keeper.onPorterStatusChanged(s1, s2, docker);
            }
        }
        // 2. heartbeat when connection expired
        if (current != null && current.equals(ConnectionState.Order.EXPIRED)) {
            heartbeat(connection);
        }
    }

    @Override
    public void onConnectionReceived(byte[] data, Connection connection) {
        Porter docker = dock(connection, true);
        if (docker == null) {
            assert false : "failed to create docker: " + connection;
        } else {
            docker.processReceived(data);
        }
    }

    @Override
    public void onConnectionSent(int sent, byte[] data, Connection connection) {
        // ignore event for sending success
    }

    @Override
    public void onConnectionFailed(IOError error, byte[] data, Connection connection) {
        // ignore event for sending failed
    }

    @Override
    public void onConnectionError(IOError error, Connection connection) {
        // ignore event for receiving error
    }
}
