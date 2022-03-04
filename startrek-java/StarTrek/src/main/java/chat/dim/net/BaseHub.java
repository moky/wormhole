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
package chat.dim.net;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.util.Set;

import chat.dim.type.AddressPairMap;

class ConnectionPool extends AddressPairMap<Connection> {

    @Override
    public void set(SocketAddress remote, SocketAddress local, Connection value) {
        Connection old = get(remote, local);
        if (old != null && old != value) {
            remove(remote, local, old);
        }
        super.set(remote, local, value);
    }

    @Override
    public Connection remove(SocketAddress remote, SocketAddress local, Connection value) {
        Connection cached = super.remove(remote, local, value);
        if (cached != null && cached.isOpen()) {
            cached.close();
        }
        return cached;
    }
}

public abstract class BaseHub implements Hub {

    /*  Maximum Segment Size
     *  ~~~~~~~~~~~~~~~~~~~~
     *  Buffer size for receiving package
     *
     *  MTU        : 1500 bytes (excludes 14 bytes ethernet header & 4 bytes FCS)
     *  IP header  :   20 bytes
     *  TCP header :   20 bytes
     *  UDP header :    8 bytes
     */
    public static int MSS = 1472;  // 1500 - 20 - 8

    private final ConnectionPool connectionPool = new ConnectionPool();
    private final WeakReference<Connection.Delegate> delegateRef;

    protected BaseHub(Connection.Delegate delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
    }

    public Connection.Delegate getDelegate() {
        return delegateRef.get();
    }

    /**
     *  Get all channels
     *
     * @return copy of channels
     */
    protected abstract Set<Channel> allChannels();

    /**
     *  Remove socket channel
     *
     * @param channel - socket channel
     */
    protected abstract void removeChannel(Channel channel);

    /**
     *  Create connection with sock channel & addresses
     *
     * @param sock   - socket channel
     * @param remote - remote address
     * @param local  - local address
     * @return null on channel not exists
     */
    protected abstract Connection createConnection(Channel sock, SocketAddress remote, SocketAddress local);

    protected Set<Connection> allConnections() {
        return connectionPool.allValues();
    }
    protected Connection getConnection(SocketAddress remote, SocketAddress local) {
        return connectionPool.get(remote, local);
    }
    protected void putConnection(Connection conn) {
        connectionPool.set(conn.getRemoteAddress(), conn.getLocalAddress(), conn);
    }
    protected void removeConnection(Connection conn) {
        connectionPool.remove(conn.getRemoteAddress(), conn.getLocalAddress(), conn);
    }

    @Override
    public Connection connect(SocketAddress remote, SocketAddress local) {
        Connection conn = getConnection(remote, local);
        if (conn != null) {
            // check local address
            if (local == null) {
                return conn;
            }
            SocketAddress address = conn.getLocalAddress();
            if (address == null || address.equals(local)) {
                return conn;
            }
            // local address not matched? ignore this connection
        }
        // try to open channel with direction (remote, local)
        Channel sock = open(remote, local);
        if (sock == null || !sock.isOpen()) {
            return null;
        }
        // create with channel
        conn = createConnection(sock, remote, local);
        if (conn != null) {
            // NOTICE: local address in the connection may be set to None
            putConnection(conn);
        }
        return conn;
    }

    protected boolean driveChannel(Channel sock) {
        ByteBuffer buffer = ByteBuffer.allocate(MSS);
        SocketAddress remote;
        // try to receive
        try {
            remote = sock.receive(buffer);
        } catch (IOException error) {
            //e.printStackTrace();
            removeChannel(sock);
            // callback
            Connection.Delegate delegate = getDelegate();
            if (delegate != null) {
                remote = sock.getRemoteAddress();
                SocketAddress local = sock.getLocalAddress();
                delegate.onError(error, null, remote, local, null);
            }
            return false;
        }
        if (remote == null) {
            // received nothing
            return false;
        }
        SocketAddress local = sock.getLocalAddress();
        // get connection for processing received data
        Connection conn = connect(remote, local);
        if (conn != null) {
            byte[] data = new byte[buffer.position()];
            buffer.flip();
            buffer.get(data);
            conn.received(data, remote, local);
        }
        return true;
    }
    protected int driveChannels(Set<Channel> channels) {
        int count = 0;
        for (Channel sock : channels) {
            if (sock.isAlive() && driveChannel(sock)) {
                // received data from this socket channel
                count += 1;
            }
        }
        return count;
    }
    protected void cleanupChannels(Set<Channel> channels) {
        for (Channel sock : channels) {
            if (!sock.isAlive()) {
                removeChannel(sock);
            }
        }
    }

    protected void driveConnections(Set<Connection> connections) {
        for (Connection conn : connections) {
            try {
                // drive connection to go on
                conn.tick();
            } catch (Throwable e) {
                e.printStackTrace();
            }
            // NOTICE: let the delegate to decide whether close an error connection
            //         or just remove it.
        }
    }
    protected void cleanupConnections(Set<Connection> connections) {
        for (Connection conn : connections) {
            if (!conn.isAlive()) {
                removeConnection(conn);
            }
        }
    }

    @Override
    public boolean process() {
        try {
            // 1. drive all channels to receive data
            Set<Channel> channels = allChannels();
            int count = driveChannels(channels);
            // 2. drive all connections to move on
            Set<Connection> connections = allConnections();
            driveConnections(connections);
            // 3. cleanup closed channels and connections
            cleanupChannels(channels);
            cleanupConnections(connections);
            return count > 0;
        } catch (Throwable e) {
            e.printStackTrace();
            return false;
        }
    }
}
