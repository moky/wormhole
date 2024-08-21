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
package chat.dim.socket;

import java.io.IOError;
import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.util.Date;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.type.AddressPairMap;

class ConnectionPool extends AddressPairMap<Connection> {

    @Override
    public Connection set(SocketAddress remote, SocketAddress local, Connection value) {
        // remove cached item
        Connection cached = super.remove(remote, local, value);
        /*/
        if (cached != null && cached != value) {
            cached.close();
        }
        /*/
        Connection old = super.set(remote, local, value);
        assert old != null : "should not happen";
        return cached;
    }

    /*/
    @Override
    public Connection remove(SocketAddress remote, SocketAddress local, Connection value) {
        Connection cached = super.remove(remote, local, value);
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

    private final WeakReference<Connection.Delegate> delegateRef;
    private final AddressPairMap<Connection> connectionPool;
    private final ReadWriteLock lock;

    protected BaseHub(Connection.Delegate gate) {
        super();
        delegateRef = new WeakReference<>(gate);
        connectionPool = createConnectionPool();
        lock = new ReentrantReadWriteLock();
    }

    protected AddressPairMap<Connection> createConnectionPool() {
        return new ConnectionPool();
    }

    // delegate for handling connection events
    protected Connection.Delegate getDelegate() {
        return delegateRef.get();
    }

    //
    //  Channel
    //

    /**
     *  Get all channels
     *
     * @return copy of channels
     */
    protected abstract Iterable<Channel> allChannels();

    /**
     *  Remove socket channel
     *
     * @param remote - remote address
     * @param local  - local address
     * @param channel - socket channel
     */
    protected abstract Channel removeChannel(SocketAddress remote, SocketAddress local, Channel channel);

    //
    //  Connection
    //

    /**
     *  Create connection with sock channel & addresses
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on channel not exists
     */
    protected abstract Connection createConnection(SocketAddress remote, SocketAddress local);

    protected Iterable<Connection> allConnections() {
        return connectionPool.allValues();
    }
    protected Connection getConnection(SocketAddress remote, SocketAddress local) {
        return connectionPool.get(remote, local);
    }
    protected Connection setConnection(SocketAddress remote, SocketAddress local, Connection conn) {
        return connectionPool.set(remote, local, conn);
    }
    protected Connection removeConnection(SocketAddress remote, SocketAddress local, Connection conn) {
        return connectionPool.remove(remote, local, conn);
    }

    @Override
    public Connection connect(SocketAddress remote, SocketAddress local) {
        //
        //  0. pre-checking
        //
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
        }
        //
        //  1. lock to check
        //
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            // check again
            conn = getConnection(remote, local);
            if (conn != null) {
                // check local address
                if (local == null) {
                    return conn;
                }
                SocketAddress address = conn.getLocalAddress();
                if (address == null || address.equals(local)) {
                    return conn;
                }
            }
            // connection not exists, or local address not matched,
            // create new connection
            conn = createConnection(remote, local);
            if (local == null) {
                local = conn.getLocalAddress();
            }
            // cache the connection
            Connection cached = setConnection(remote, local, conn);
            if (cached != null && cached != conn) {
                cached.close();
            }
        } finally {
            writeLock.unlock();
        }
        //
        //  2. start the new connection
        //
        if (conn instanceof BaseConnection) {
            // try to open channel with direction (remote, local)
            ((BaseConnection) conn).start(this);
        } else {
            assert false : "connection error: " + remote + ", " + conn;
        }
        return conn;
    }

    //
    //  Process
    //

    protected void closeChannel(Channel sock) {
        try {
            if (sock.isOpen()) {
                sock.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    protected boolean driveChannel(Channel sock) {
        //
        //  0. check channel state
        //
        Channel.Status cs = sock.getStatus();
        if (Channel.Status.INIT.equals(cs)) {
            // preparing
            return false;
        } else if (Channel.Status.CLOSED.equals(cs)) {
            // finished
            return false;
        }
        // cs == opened
        // cs == alive
        ByteBuffer buffer = ByteBuffer.allocate(MSS);
        SocketAddress remote;
        SocketAddress local;
        //
        //  1. try to receive
        //
        try {
            remote = sock.receive(buffer);
        } catch (IOException ex) {
            //e.printStackTrace();
            remote = sock.getRemoteAddress();
            local = sock.getLocalAddress();
            Connection.Delegate gate = getDelegate();
            Channel cached;
            if (gate == null || remote == null) {
                // UDP channel may not connected,
                // so no connection for it
                cached = removeChannel(remote, local, sock);
            } else {
                // remove channel and callback with connection
                Connection conn = getConnection(remote, local);
                cached = removeChannel(remote, local, sock);
                if (conn != null) {
                    gate.onConnectionError(new IOError(ex), conn);
                }
            }
            // close removed/error channels
            if (cached != null && cached != sock) {
                closeChannel(cached);
            }
            closeChannel(sock);
            return false;
        }
        if (remote == null) {
            // received nothing
            return false;
        } else {
            assert buffer.position() > 0 : "data should not empty: " + remote;
            local = sock.getLocalAddress();
        }
        //
        //  2. get connection for processing received data
        //
        Connection conn = connect(remote, local);
        if (conn != null) {
            byte[] data = new byte[buffer.position()];
            buffer.flip();
            buffer.get(data);
            conn.onReceived(data);
        }
        return true;
    }
    protected int driveChannels(Iterable<Channel> channels) {
        int count = 0;
        for (Channel sock : channels) {
            // drive channel to receive data
            if (driveChannel(sock)) {
                count += 1;
            }
        }
        return count;
    }
    protected void cleanupChannels(Iterable<Channel> channels) {
        Channel cached;
        for (Channel sock : channels) {
            if (!sock.isOpen()) {
                // if channel not connected (TCP) and not bound (UDP),
                // means it's closed, remove it from the hub
                cached = removeChannel(sock.getRemoteAddress(), sock.getLocalAddress(), sock);
                if (cached != null && cached != sock) {
                    closeChannel(cached);
                }
            }
        }
    }

    private Date last = new Date();

    protected void driveConnections(Iterable<Connection> connections) {
        Date now = new Date();
        long delta = now.getTime() - last.getTime();
        for (Connection conn : connections) {
            // drive connection to go on
            conn.tick(now, delta);
            // NOTICE: let the delegate to decide whether close an error connection
            //         or just remove it.
        }
        last = now;
    }
    protected void cleanupConnections(Iterable<Connection> connections) {
        Connection cached;
        for (Connection conn : connections) {
            if (!conn.isOpen()) {
                // if connection closed, remove it from the hub; notice that
                // ActiveConnection can reconnect, it'll be not connected
                // but still open, don't remove it in this situation.
                cached = removeConnection(conn.getRemoteAddress(), conn.getLocalAddress(), conn);
                if (cached != null && cached != conn) {
                    cached.close();
                }
            }
        }
    }

    @Override
    public boolean process() {
        // 1. drive all channels to receive data
        Iterable<Channel> channels = allChannels();
        int count = driveChannels(channels);
        // 2. drive all connections to move on
        Iterable<Connection> connections = allConnections();
        driveConnections(connections);
        // 3. cleanup closed channels and connections
        cleanupChannels(channels);
        cleanupConnections(connections);
        return count > 0;
    }

}
