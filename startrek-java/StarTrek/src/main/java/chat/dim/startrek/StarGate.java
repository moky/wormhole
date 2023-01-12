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
import java.util.List;
import java.util.Set;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.port.Gate;
import chat.dim.type.AddressPairMap;

class DockerPool extends AddressPairMap<Docker> {

    @Override
    public void set(SocketAddress remote, SocketAddress local, Docker value) {
        Docker old = get(remote, local);
        if (old != null && old != value) {
            remove(remote, local, old);
        }
        super.set(remote, local, value);
    }

    @Override
    public Docker remove(SocketAddress remote, SocketAddress local, Docker value) {
        Docker cached = super.remove(remote, local, value);
        if (cached != null && cached.isOpen()) {
            cached.close();
        }
        return cached;
    }
}

public abstract class StarGate implements Gate, Connection.Delegate {

    private final AddressPairMap<Docker> dockerPool;
    private final WeakReference<Docker.Delegate> delegateRef;

    protected StarGate(Docker.Delegate delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
        dockerPool = createDockerPool();
    }

    protected AddressPairMap<Docker> createDockerPool() {
        return new DockerPool();
    }

    // delegate for handling docker events
    protected Docker.Delegate getDelegate() {
        return delegateRef.get();
    }

    @Override
    public boolean sendData(byte[] payload, SocketAddress remote, SocketAddress local) {
        Docker docker = getDocker(remote, local);
        if (docker == null || !docker.isOpen()) {
            return false;
        }
        return docker.sendData(payload);
    }

    @Override
    public boolean sendShip(Departure outgo, SocketAddress remote, SocketAddress local) {
        Docker docker = getDocker(remote, local);
        if (docker == null || !docker.isOpen()) {
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
     * @param conn   - current connection
     * @param data   - advance party
     * @return docker
     */
    protected abstract Docker createDocker(Connection conn, List<byte[]> data);

    protected Set<Docker> allDockers() {
        return dockerPool.allValues();
    }

    protected Docker getDocker(SocketAddress remote, SocketAddress local) {
        return dockerPool.get(remote, local);
    }

    protected void setDocker(SocketAddress remote, SocketAddress local, Docker docker) {
        dockerPool.set(remote, local, docker);
    }

    protected void removeDocker(SocketAddress remote, SocketAddress local, Docker docker) {
        dockerPool.remove(remote, local, docker);
    }

    //
    //  Processor
    //

    @Override
    public boolean process() {
        Set<Docker> dockers = allDockers();
        // 1. drive all dockers to process
        int count = driveDockers(dockers);
        // 2. cleanup for dockers
        cleanupDockers(dockers);
        return count > 0;
    }
    protected int driveDockers(Set<Docker> dockers) {
        int count = 0;
        for (Docker worker : dockers) {
            if (worker.process()) {
                ++count;  // it's busy
            }
        }
        return count;
    }
    protected void cleanupDockers(Set<Docker> dockers) {
        for (Docker worker : dockers) {
            if (worker.isOpen()) {
                // clear expired tasks
                worker.purge();
            } else {
                // remove docker when connection closed
                removeDocker(worker.getRemoteAddress(), worker.getLocalAddress(), worker);
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
    public void onConnectionStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        // 1. callback when status changed
        Docker.Delegate delegate = getDelegate();
        if (delegate != null) {
            Docker.Status s1 = Docker.Status.getStatus(previous);
            Docker.Status s2 = Docker.Status.getStatus(current);
            // check status
            boolean changed;
            if (s1 == null) {
                changed = s2 != null;
            } else if (s2 == null) {
                changed = true;
            } else {
                changed = !s1.equals(s2);
            }
            if (changed) {
                // callback
                SocketAddress remote = connection.getRemoteAddress();
                SocketAddress local = connection.getLocalAddress();
                Docker docker = getDocker(remote, local);
                // NOTICE: if the previous state is null, the docker maybe not
                //         created yet, this situation means the docker status
                //         not changed too, so no need to callback here.
                if (docker != null) {
                    delegate.onDockerStatusChanged(s1, s2, docker);
                }
            }
        }
        // 2. heartbeat when connection expired
        if (current != null && current.equals(ConnectionState.EXPIRED)) {
            heartbeat(connection);
        }
    }

    @Override
    public void onConnectionReceived(byte[] data, Connection connection) {
        SocketAddress remote = connection.getRemoteAddress();
        SocketAddress local = connection.getLocalAddress();
        // get docker by (remote, local)
        Docker worker = getDocker(remote, local);
        if (worker != null) {
            // docker exists, call docker.onReceived(data);
            worker.processReceived(data);
            return;
        }

        // cache advance party for this connection
        List<byte[]> advanceParty = cacheAdvanceParty(data, connection);
        assert advanceParty != null && advanceParty.size() > 0 : "advance party error";

        // docker not exists, check the data to decide which docker should be created
        worker = createDocker(connection, advanceParty);
        if (worker != null) {
            // cache docker for (remote, local)
            setDocker(worker.getRemoteAddress(), worker.getLocalAddress(), worker);
            // process advance parties one by one
            for (byte[] part : advanceParty) {
                worker.processReceived(part);
            }
            // remove advance party
            clearAdvanceParty(connection);
        }
    }

    // cache the advance party before decide which docker to use
    protected abstract List<byte[]> cacheAdvanceParty(byte[] data, Connection connection);
    protected abstract void clearAdvanceParty(Connection connection);

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
