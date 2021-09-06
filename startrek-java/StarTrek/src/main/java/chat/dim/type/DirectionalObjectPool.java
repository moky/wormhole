/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
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
package chat.dim.type;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public abstract class DirectionalObjectPool<C> {

    public static final SocketAddress anyLocalAddress = new InetSocketAddress("0.0.0.0", 0);
    public static final SocketAddress anyRemoteAddress = new InetSocketAddress("0.0.0.0", 0);

    private final ReadWriteLock lock = new ReentrantReadWriteLock();
    private final Set<C> connections = new HashSet<>();
    // because the remote address will always different to local address, so
    // we shared the same map for all directions here:
    //    mapping: (remote, local) => Connection
    //    mapping: (remote, null) => Connection
    //    mapping: (local, null) => Connection
    private final Map<SocketAddress, Map<SocketAddress, C>> map = new HashMap<>();

    public Set<C> all() {
        Set<C> candidates = new HashSet<>();
        Lock readLock = lock.readLock();
        readLock.lock();
        try {
            candidates.addAll(connections);
        } finally {
            readLock.unlock();
        }
        return candidates;
    }

    /**
     *  Create connection from local to remote
     *
     * @param remote - remote address
     * @param local  - local address
     * @return connected/bound connection
     */
    protected abstract C create(SocketAddress remote, SocketAddress local) throws IOException;

    public C seek(SocketAddress remote, SocketAddress local, boolean create) throws IOException {
        C conn;
        Lock readLock = lock.readLock();
        readLock.lock();
        try {
            // double check to make sure the connection doesn't exist
            conn = seek(remote, local);
            if (conn == null && create) {
                // create it
                conn = create(remote, local);
                if (conn != null) {
                    // make sure different connection with same pair(remote, local) not exists
                    connections.remove(conn);
                    // cache it
                    connections.add(conn);
                    // create indexes for this connection
                    createIndexes(conn, remote, local);
                }
            }
        } finally {
            readLock.unlock();
        }
        return conn;
    }

    private C seek(SocketAddress remote, SocketAddress local) {
        Map<SocketAddress, C> table;
        Iterator<C> it;
        C conn;
        if (remote == null) {
            assert local != null : "local & remote addresses should not empty at the same time";
            // get object bound to local address
            table = map.get(local);
            if (table == null) {
                return null;
            } else {
                // mapping: (local, null) => Connection
                conn = table.get(anyRemoteAddress);
                if (conn != null) {
                    return conn;
                }
            }
        } else {
            // get objects connected to remote address
            table = map.get(remote);
            if (table == null) {
                return null;
            } else if (local != null) {
                // mapping: (remote, local) => Connection
                return table.get(local);
            } else {
                // mapping: (remote, null) => Connection
                conn = table.get(anyLocalAddress);
                if (conn != null) {
                    return conn;
                }
            }
        }
        // get any object bound/connected to the local/remote address
        it = table.values().iterator();
        return it.hasNext() ? it.next() : null;
    }

    public void update(C conn, SocketAddress remote, SocketAddress local) {
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            // make sure different connection with same pair(remote, local) not exists
            connections.remove(conn);
            // cache it
            connections.add(conn);
            // create indexes for this connection
            createIndexes(conn, remote, local);
        } finally {
            writeLock.unlock();
        }
    }

    public void remove(C conn, SocketAddress remote, SocketAddress local) {
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            connections.remove(conn);
            removeIndexes(remote, local);
        } finally {
            writeLock.unlock();
        }
    }

    private void createIndexes(C conn, SocketAddress remote, SocketAddress local) {
        Map<SocketAddress, C> table;
        if (remote == null) {
            assert local != null : "local & remote addresses should not empty at the same time";
            // get table for local address
            table = map.get(local);
            if (table == null) {
                table = new WeakHashMap<>();
                map.put(local, table);
            }
            // mapping: (local, null) => Connection
            table.put(anyRemoteAddress, conn);
        } else {
            // get table for remote address
            table = map.get(remote);
            if (table == null) {
                table = new WeakHashMap<>();
                map.put(remote, table);
            }
            if (local == null) {
                // mapping: (remote, null) => Connection
                table.put(anyLocalAddress, conn);
            } else {
                // mapping: (remote, local) => Connection
                table.put(local, conn);
            }
        }
    }

    private void removeIndexes(SocketAddress remote, SocketAddress local) {
        Map<SocketAddress, C> table;
        if (remote == null) {
            assert local != null : "local & remote addresses should not empty at the same time";
            // get table for local address
            table = map.get(local);
            if (table != null) {
                // mapping: (local, null) => Connection
                table.remove(anyRemoteAddress);
            }
        } else {
            // get table for remote address
            table = map.get(remote);
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
}
