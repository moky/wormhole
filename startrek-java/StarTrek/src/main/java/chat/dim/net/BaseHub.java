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

    private final AddressPairMap<Connection> connectionPool = new AddressPairMap<>();

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

    @Override
    public Connection connect(SocketAddress remote, SocketAddress local) {
        Connection conn = connectionPool.get(remote, local);
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
        Channel sock = openChannel(remote, local);
        if (sock == null || !sock.isOpen()) {
            return null;
        }
        // create with channel
        conn = createConnection(sock, remote, local);
        if (conn != null) {
            // NOTICE: local address in the connection may be set to None
            local = conn.getLocalAddress();
            remote = conn.getRemoteAddress();
            connectionPool.put(remote, local, conn);
        }
        return conn;
    }

    @Override
    public Connection disconnect(SocketAddress remote, SocketAddress local, Connection connection) {
        Connection conn = removeConnection(remote, local, connection);
        if (conn != null) {
            conn.close();
        }
        if (connection != null && connection != conn) {
            connection.close();
        }
        return conn == null ? connection : conn;
    }

    private Connection removeConnection(SocketAddress remote, SocketAddress local, Connection conn) {
        if (conn == null) {
            assert remote != null : "remote address should not be empty";
            conn = connectionPool.get(remote, local);
            if (conn == null) {
                // connection not exists
                return null;
            }
        }
        // check local address
        if (local != null) {
            SocketAddress address = conn.getLocalAddress();
            if (address != null && !address.equals(local)) {
                // local address not matched
                return null;
            }
        }
        remote = conn.getRemoteAddress();
        local = conn.getLocalAddress();
        return connectionPool.remove(remote, local, conn);
    }

    @Override
    public boolean process() {
        // 1. drive all channels to receive data
        Set<Channel> channels = allChannels();
        int count = driveChannels(channels);
        cleanupChannels(channels);
        // 2. drive all connections to move on
        Set<Connection> connections = allConnections();
        driveConnections(connections);
        cleanupConnections(connections);
        return count > 0;
    }

    protected int driveChannels(Set<Channel> channels) {
        int count = 0;
        for (Channel sock : channels) {
            // update channel status
            sock.tick();
            if (!sock.isAlive()) {
                continue;
            }
            if (drive(sock)) {
                // received data from this socket channel
                count += 1;
            }
        }
        return count;
    }
    protected boolean drive(Channel sock) {
        SocketAddress local = sock.getLocalAddress();
        SocketAddress remote;
        final ByteBuffer buffer = ByteBuffer.allocate(MSS);
        // try to receive
        try {
            remote = sock.receive(buffer);
        } catch (IOException e) {
            //e.printStackTrace();
            remote = sock.getRemoteAddress();
            // socket error, remove the channel
            closeChannel(sock);
            // callback
            Connection.Delegate delegate = getDelegate();
            if (delegate != null) {
                delegate.onError(e, null, remote, local, null);
            }
            return false;
        }
        if (remote == null) {
            // received nothing
            return false;
        }
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
    protected void cleanupChannels(Set<Channel> channels) {
        // TODO: remove closed channel
    }

    protected void driveConnections(Set<Connection> connections) {
        for (Connection conn : connections) {
            // drive connection to go on
            conn.tick();
            // NOTICE: let the delegate to decide whether close an error connection
            //         or just remove it.
        }
    }
    protected void cleanupConnections(Set<Connection> connections) {
        // TODO: remove closed connection
    }
}
