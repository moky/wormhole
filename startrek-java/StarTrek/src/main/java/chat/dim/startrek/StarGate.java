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
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.port.Docker;
import chat.dim.port.Gate;
import chat.dim.skywalker.Runner;
import chat.dim.type.AddressPairMap;

public abstract class StarGate extends Runner implements Gate, Connection.Delegate {

    private final AddressPairMap<Docker> dockerPool = new AddressPairMap<>();

    private final Map<SocketAddress, List<byte[]>> advanceParties = new HashMap<>();

    private final WeakReference<Delegate> delegateRef;

    protected StarGate(Delegate delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
    }

    protected abstract Connection getConnection(SocketAddress remote, SocketAddress local);
    protected abstract Connection connect(SocketAddress remote, SocketAddress local) throws IOException;

    // create new Docker with data (advance party)
    protected abstract Docker createDocker(SocketAddress remote, SocketAddress local, List<byte[]> data);

    public Docker getDocker(SocketAddress remote, SocketAddress local, boolean create) {
        Docker worker = dockerPool.get(remote, local);
        if (worker == null && create) {
            List<byte[]> data = advanceParties.get(remote);
            worker = createDocker(remote, local, data);
            if (worker != null) {
                dockerPool.put(remote, local, worker);
                // docker created, remove cache data
                advanceParties.remove(remote);
            }
        }
        return worker;
    }
    protected void setDocker(Docker worker, SocketAddress remote, SocketAddress local) {
        dockerPool.put(remote, local, worker);
    }

    public Gate.Delegate getDelegate() {
        return delegateRef.get();
    }

    @Override
    public Status getStatus(SocketAddress remote, SocketAddress local) {
        Connection conn = getConnection(remote, local);
        return conn == null ? Status.ERROR : Status.getStatus(conn.getState());
    }

    @Override
    public boolean send(byte[] data, SocketAddress source, SocketAddress destination) throws IOException {
        Connection conn = connect(destination, source);
        if (conn == null) {
            return false;
        }
        Status status = Status.getStatus(conn.getState());
        if (!status.equals(Status.READY)) {
            return false;
        }
        return conn.send(data, destination) != -1;
    }

    //
    //  Runner
    //

    @Override
    public boolean process() {
        int counter = 0;
        Set<Docker> dockers = dockerPool.allValues();
        SocketAddress remote, local;
        for (Docker worker : dockers) {
            remote = worker.getRemoteAddress();
            local = worker.getLocalAddress();
            // check connection
            if (getConnection(remote, local) == null) {
                // connection lost, remove worker
                dockerPool.remove(remote, local, worker);
            } else if (worker.process()) {
                counter += 1;
            }
        }
        return counter > 0;
    }

    /**
     *  Send a heartbeat package('PING') to remote address
     */
    protected void heartbeat(Connection connection) throws IOException {
        SocketAddress remote = connection.getRemoteAddress();
        SocketAddress local = connection.getLocalAddress();
        Docker worker = getDocker(remote, local, false);
        if (worker != null) {
            worker.heartbeat();
        }
    }

    //
    //  Connection Delegate
    //

    @Override
    public void onStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        // heartbeat when connection expired
        if (current != null && current.equals(ConnectionState.EXPIRED)) {
            try {
                heartbeat(connection);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        // callback when status changed
        Delegate delegate = getDelegate();
        if (delegate != null) {
            Status s1 = Status.getStatus(previous);
            Status s2 = Status.getStatus(current);
            if (!s1.equals(s2)) {
                delegate.onStatusChanged(s1, s2, connection.getRemoteAddress(), this);
            }
        }
    }

    @Override
    public void onReceived(byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        // get docker by remote address
        Docker worker = getDocker(source, destination, false);
        if (worker == null) {
            // save advance parties from this source address
            List<byte[]> parties = advanceParties.get(source);
            if (parties == null) {
                parties = new ArrayList<>();
            }
            parties.add(data);
            advanceParties.put(source, parties);
            // docker not exists, check the data to decide which docker should be created
            worker = getDocker(source, destination, true);
            if (worker != null) {
                // the data has already moved into the docker (use data to initialize)
                // so here pass nothing to process
                worker.process(null);
            }
        } else {
            // docker exists, call docker.process(data);
            worker.process(data);
        }
    }

    @Override
    public void onSent(byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {

    }

    @Override
    public void onError(Throwable error, byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {

    }
}
