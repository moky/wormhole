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
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.port.Gate;
import chat.dim.skywalker.Runner;

public abstract class StarGate<D extends Departure<A, I>, A extends Arrival<A, I>, I>
        extends Runner implements Gate, Connection.Delegate {

    private final Map<SocketAddress, Docker<D, A, I>> dockerMap = new HashMap<>();

    private final WeakReference<Delegate<D, A, I>> delegateRef;

    protected StarGate(Delegate<D, A, I> delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
    }

    protected abstract Connection getConnection(SocketAddress remote);
    protected abstract Connection connect(SocketAddress remote) throws IOException;

    // create new Docker with data (advance party)
    protected abstract Docker<D, A, I> createDocker(SocketAddress remote, byte[] data);

    public Docker<D, A, I> getDocker(SocketAddress remote) {
        return dockerMap.get(remote);
    }
    protected void setDocker(SocketAddress remote, Docker<D, A, I> worker) {
        if (worker == null) {
            // remove worker
            worker = dockerMap.get(remote);
            if (worker != null) {
                dockerMap.remove(remote);
            }
        } else {
            // set worker
            dockerMap.put(remote, worker);
        }
    }

    public Gate.Delegate<D, A, I> getDelegate() {
        return delegateRef.get();
    }

    @Override
    public Status getStatus(SocketAddress remote) {
        Connection conn = getConnection(remote);
        return conn == null ? Status.ERROR : Status.getStatus(conn.getState());
    }

    @Override
    public boolean send(byte[] data, SocketAddress remote) throws IOException {
        Connection conn = connect(remote);
        if (conn == null) {
            return false;
        }
        Status status = Status.getStatus(conn.getState());
        if (!status.equals(Status.READY)) {
            return false;
        }
        return conn.send(data, remote) != -1;
    }

    //
    //  Runner
    //

    @Override
    public boolean process() {
        int counter = 0;
        Map.Entry<SocketAddress, Docker<D, A, I>> entry;
        Docker<D, A, I> worker;
        Iterator<Map.Entry<SocketAddress, Docker<D, A, I>>> iterator;
        iterator = dockerMap.entrySet().iterator();
        while (iterator.hasNext()) {
            entry = iterator.next();
            if (getConnection(entry.getKey()) == null) {
                iterator.remove();
                continue;
            }
            worker = entry.getValue();
            if (worker != null && worker.process()) {
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
        Docker<D, A, I> worker = getDocker(remote);
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
        Delegate<D, A, I> delegate = getDelegate();
        if (delegate != null) {
            Status s1 = Status.getStatus(previous);
            Status s2 = Status.getStatus(current);
            if (!s1.equals(s2)) {
                delegate.onStatusChanged(s1, s2, connection.getRemoteAddress(), this);
            }
        }
    }

    @Override
    public void onReceived(byte[] data, SocketAddress remote, Connection connection) {
        // get docker by remote address
        Docker<D, A, I> worker = getDocker(remote);
        if (worker == null) {
            // docker not exists, check the data to decide which docker should be created
            worker = createDocker(remote, data);
            if (worker != null) {
                setDocker(remote, worker);
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
    public void onSent(byte[] data, SocketAddress remote, Connection connection) {

    }

    @Override
    public void onError(Throwable error, byte[] data, SocketAddress remote, Connection connection) {

    }
}
