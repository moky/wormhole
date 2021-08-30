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

import javafx.util.Pair;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.threading.Ticker;

public abstract class BaseHub implements Hub, Ticker {

    private final SocketAddress anyLocalAddress = new InetSocketAddress("0.0.0.0", 0);
    private final SocketAddress anyRemoteAddress = new InetSocketAddress("0.0.0.0", 0);

    private final ReentrantReadWriteLock connectionLock = new ReentrantReadWriteLock();
    private final Set<Connection> connectionSet = new HashSet<>();
    // because the remote address will always different to local address, so
    // we shared the same map for all directions here:
    //    mapping: (remote, local) => Connection
    //    mapping: (remote, null) => Connection
    //    mapping: (local, null) => Connection
    private final Map<SocketAddress, Map<SocketAddress, Connection>> connectionMap = new HashMap<>();

    // mapping: (remote, local) => time to kill
    private final Map<Pair<SocketAddress, SocketAddress>, Long> dyingTimes = new HashMap<>();
    public static long DYING_EXPIRES = 120 * 1000;

    @Override
    public boolean send(byte[] data, SocketAddress source, SocketAddress destination) throws IOException {
        Connection conn = connect(destination, source);
        if (conn == null || !conn.isOpen()) {
            // connection closed
            return false;
        }
        return conn.send(data, destination) != -1;
    }

    @Override
    public Connection getConnection(SocketAddress remote, SocketAddress local) {
        Connection conn;
        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            conn = seekConnection(remote, local);
        } finally {
            readLock.unlock();
        }
        return conn;
    }

    @Override
    public Connection connect(SocketAddress remote, SocketAddress local) throws IOException {
        assert local != null || remote != null : "both local & remote addresses are empty";
        // 1. try to get connection from cache pool
        Connection conn = getConnection(remote, local);
        if (conn != null) {
            return conn;
        }
        // 2. connection not found, try to create connection
        Lock writeLock = connectionLock.writeLock();
        writeLock.lock();
        try {
            // double check to make sure the connection doesn't exist
            conn = seekConnection(remote, local);
            if (conn == null) {
                // create it
                conn = createConnection(remote, local);
                if (createIndexesForConnection(conn, remote, local)) {
                    // make sure different connection with same pair(remote, local) not exists
                    connectionSet.remove(conn);
                    // cache it
                    connectionSet.add(conn);
                }
            }
        } finally {
            writeLock.unlock();
        }
        return conn;
    }
    protected abstract Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException;

    @Override
    public void disconnect(SocketAddress remote, SocketAddress local) throws IOException {
        assert local != null || remote != null : "both local & remote addresses are empty";
        Connection conn;
        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            conn = seekConnection(remote, local);
        } finally {
            readLock.unlock();
        }
        if (conn != null) {
            conn.close();
            removeConnection(conn);
        }
    }

    @Override
    public void tick() {
        Set<Connection> connections = new HashSet<>();
        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            connections.addAll(connectionSet);
        } finally {
            readLock.unlock();
        }

        Pair<SocketAddress, SocketAddress> aPair;  // (remote, local)
        long now = (new Date()).getTime();
        Long expired;
        for (Connection conn : connections) {
            // call 'tick()' to drive all connections
            conn.tick();
            // check closed connection(s)
            aPair = buildPair(conn.getRemoteAddress(), conn.getLocalAddress());
            if (aPair == null) {
                // should not happen
                removeConnection(conn);
            } else if (conn.isOpen()) {
                // connection still alive, revive it
                dyingTimes.remove(aPair);
            } else {
                // connection is closed, check dying time
                expired = dyingTimes.get(aPair);
                if (expired == null || expired == 0) {
                    // set death clock
                    dyingTimes.put(aPair, now + DYING_EXPIRES);
                } else if (expired < now) {
                    // times up, kill it
                    removeConnection(conn);
                    // clear the death clock for it
                    dyingTimes.remove(aPair);
                }
            }
        }
    }
    private Pair<SocketAddress, SocketAddress> buildPair(SocketAddress remote, SocketAddress local) {
        if (remote == null) {
            if (local == null) {
                //throw new NullPointerException("both local & remote addresses are empty");
                return null;
            }
            return new Pair<>(anyRemoteAddress, local);
        } else if (local == null) {
            return new Pair<>(remote, anyLocalAddress);
        } else {
            return new Pair<>(remote, local);
        }
    }

    private Connection seekConnection(SocketAddress remote, SocketAddress local) {
        if (remote == null) {
            assert local != null : "both local & remote addresses are empty";
            // get connection bound to local address
            Map<SocketAddress, Connection> table = connectionMap.get(local);
            if (table == null) {
                return null;
            } else {
                // mapping: (local, null) => Connection
                Connection conn = table.get(anyRemoteAddress);
                if (conn != null) {
                    return conn;
                }
            }
            // get any connection bound to this local address
            Iterator<Connection> it = table.values().iterator();
            return it.hasNext() ? it.next() : null;
        } else {
            // get connections connected to remote address
            Map<SocketAddress, Connection> table = connectionMap.get(remote);
            if (table == null) {
                return null;
            } else if (local != null) {
                // mapping: (remote, local) => Connection
                return table.get(local);
            } else {
                // mapping: (remote, null) => Connection
                Connection conn = table.get(anyLocalAddress);
                if (conn != null) {
                    return conn;
                }
            }
            // get any connection connected to this remote address
            Iterator<Connection> it = table.values().iterator();
            return it.hasNext() ? it.next() : null;
        }
    }
    private boolean createIndexesForConnection(Connection conn, SocketAddress remote, SocketAddress local) {
        if (remote == null) {
            if (local == null) {
                //throw new NullPointerException("both local & remote addresses are empty");
                return false;
            }
            // get table for local address
            Map<SocketAddress, Connection> table = connectionMap.get(local);
            if (table == null) {
                table = new WeakHashMap<>();
                connectionMap.put(local, table);
            }
            // mapping: (local, null) => Connection
            table.put(anyRemoteAddress, conn);
        } else {
            // get table for remote address
            Map<SocketAddress, Connection> table = connectionMap.get(remote);
            if (table == null) {
                table = new WeakHashMap<>();
                connectionMap.put(remote, table);
            }
            if (local == null) {
                // mapping: (remote, null) => Connection
                table.put(anyLocalAddress, conn);
            } else {
                // mapping: (remote, local) => Connection
                table.put(local, conn);
            }
        }
        return true;
    }
    private void removeIndexesForConnection(Connection conn) {
        SocketAddress remote = conn.getRemoteAddress();
        SocketAddress local = conn.getLocalAddress();
        if (remote == null) {
            if (local == null) {
                //throw new NullPointerException("both local & remote addresses are empty");
                return;
            }
            // get table for local address
            Map<SocketAddress, Connection> table = connectionMap.get(local);
            if (table != null) {
                // mapping: (local, null) => Connection
                table.remove(anyRemoteAddress);
            }
        } else {
            // get table for remote address
            Map<SocketAddress, Connection> table = connectionMap.get(remote);
            if (table != null) {
                if (local == null) {
                    // mapping: (remote, null) => Connection
                    table.remove(anyLocalAddress);
                } else {
                    // mapping: (remote, local) => Connection
                    table.remove(local);
                }
            }
        }
    }
    private void removeConnection(Connection conn) {
        Lock writeLock = connectionLock.writeLock();
        writeLock.lock();
        try {
            connectionSet.remove(conn);
            removeIndexesForConnection(conn);
        } finally {
            writeLock.unlock();
        }
    }
}
