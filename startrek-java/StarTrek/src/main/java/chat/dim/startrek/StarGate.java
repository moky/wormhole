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

import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.List;
import java.util.Set;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.port.Docker;
import chat.dim.port.Gate;
import chat.dim.type.AddressPairMap;

public abstract class StarGate implements Gate, Connection.Delegate {

    private final AddressPairMap<Docker> dockerPool = new AddressPairMap<>();

    private final WeakReference<Delegate> delegateRef;

    protected StarGate(Delegate delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
    }

    @Override
    public Delegate getDelegate() {
        return delegateRef.get();
    }

    /**
     *  Create new docker for received data
     *
     * @param remote - remote address
     * @param local  - local address
     * @param data   - advance party
     * @return docker
     */
    protected abstract Docker createDocker(SocketAddress remote, SocketAddress local, List<byte[]> data);

    protected void removeDocker(SocketAddress remote, SocketAddress local, Docker docker) {
        dockerPool.remove(remote, local, docker);
    }

    protected void putDocker(Docker docker) {
        SocketAddress remote = docker.getRemoteAddress();
        SocketAddress local = docker.getLocalAddress();
        dockerPool.put(remote, local, docker);
    }

    protected Docker getDocker(SocketAddress remote, SocketAddress local) {
        return dockerPool.get(remote, local);
    }

    @Override
    public Status getStatus(SocketAddress remote, SocketAddress local) {
        Connection conn = getConnection(remote, local);
        return conn == null ? Status.ERROR : Status.getStatus(conn.getState());
    }

    //
    //  Processor
    //

    @Override
    public boolean process() {
        Set<Docker> dockers = dockerPool.allValues();
        // 1. drive all dockers to process
        int count = drive(dockers);
        // 2 remove retired dockers
        cleanup(dockers);
        return count > 0;
    }
    protected int drive(Set<Docker> dockers) {
        int count = 0;
        for (Docker worker : dockers) {
            if (worker.process()) {
                // it's busy
                ++count;
            }
        }
        return count;
    }
    protected void cleanup(Set<Docker> dockers) {
        SocketAddress remote, local;
        Connection conn;
        ConnectionState state;
        for (Docker worker : dockers) {
            remote = worker.getRemoteAddress();
            local = worker.getLocalAddress();
            // check connection state
            conn = getConnection(remote, local);
            if (conn == null) {
                state = null;
            } else {
                state = conn.getState();
            }
            if (state == null || state.equals(ConnectionState.ERROR)) {
                // connection lost, remove worker
                removeDocker(remote, local, worker);
            } else {
                // clear expired tasks
                worker.purge();
            }
        }
    }

    /**
     *  Send a heartbeat package('PING') to remote address
     */
    protected void heartbeat(Connection connection) {
        SocketAddress remote = connection.getRemoteAddress();
        SocketAddress local = connection.getLocalAddress();
        Docker worker = getDocker(remote, local);
        if (worker != null) {
            worker.heartbeat();
        }
    }

    //
    //  Connection Delegate
    //

    @Override
    public void onStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        SocketAddress remote = connection.getRemoteAddress();
        SocketAddress local = connection.getLocalAddress();
        if (current == null || current.equals(ConnectionState.ERROR)) {
            // connection lost, remove the docker for it
            removeDocker(remote, local, null);
        } else if (current.equals(ConnectionState.EXPIRED)) {
            // heartbeat when connection expired
            heartbeat(connection);
        }
        // callback when status changed
        Delegate delegate = getDelegate();
        Status s1 = Status.getStatus(previous);
        Status s2 = Status.getStatus(current);
        if (!s1.equals(s2) && delegate != null) {
            delegate.onStatusChanged(s1, s2, remote, local, this);
        }
    }

    @Override
    public void onReceived(byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        // get docker by (remote, local)
        Docker worker = getDocker(source, destination);
        if (worker != null) {
            // docker exists, call docker.onReceived(data);
            worker.processReceived(data);
            return;
        }

        // save advance party from this source address
        List<byte[]> advanceParty = cacheAdvanceParty(data, source, destination, connection);
        assert advanceParty != null && advanceParty.size() > 0 : "advance party error";

        // docker not exists, check the data to decide which docker should be created
        worker = createDocker(source, destination, advanceParty);
        if (worker != null) {
            // cache docker for (remote, local)
            putDocker(worker);
            // process advance parties one by one
            for (byte[] part : advanceParty) {
                worker.processReceived(part);
            }
            // remove advance party
            clearAdvanceParty(source, destination, connection);
        }
    }

    // cache the advance party before decide which docker to use
    protected abstract List<byte[]> cacheAdvanceParty(byte[] data, SocketAddress source, SocketAddress destination, Connection connection);
    protected abstract void clearAdvanceParty(SocketAddress source, SocketAddress destination, Connection connection);

    @Override
    public void onSent(byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        // ignore this event
    }

    @Override
    public void onError(Throwable error, byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        // failed to send data
        if (error != null && destination != null) {
            removeDocker(destination, source, null);
        }
    }
}
