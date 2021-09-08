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
package chat.dim.net;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.Set;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.type.AddressPairMap;

/**
 *  Connection Pool
 *  ~~~~~~~~~~~~~~~
 */
class ConnectionPool {

    private final ReadWriteLock lock = new ReentrantReadWriteLock();
    private final AddressPairMap<Connection> map = new AddressPairMap<>();

    private final WeakReference<BaseHub> delegate;

    ConnectionPool(BaseHub hub) {
        super();
        delegate = new WeakReference<>(hub);
    }

    private BaseHub getHub() {
        return delegate.get();
    }

    Set<Connection> all() {
        Set<Connection> connections;
        Lock readLock = lock.readLock();
        readLock.lock();
        try {
            connections = map.allValues();
        } finally {
            readLock.unlock();
        }
        return connections;
    }

    Connection get(SocketAddress remote, SocketAddress local, boolean create) throws IOException {
        assert local != null || remote != null : "both local & remote addresses are empty";
        Connection conn;
        if (create) {
            Lock readLock = lock.readLock();
            readLock.lock();
            try {
                conn = map.get(remote, local);
            } finally {
                readLock.unlock();
            }
        } else {
            Lock writeLock = lock.writeLock();
            writeLock.lock();
            try {
                conn = map.get(remote, local);
                if (conn == null) {
                    conn = getHub().createConnection(remote, local);
                    if (conn != null) {
                        map.put(remote, local, conn);
                    }
                }
            } finally {
                writeLock.unlock();
            }
        }
        return conn;
    }

    Connection remove(SocketAddress remote, SocketAddress local, Connection conn) {
        assert local != null || remote != null : "both local & remote addresses are empty";
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            if (conn == null) {
                conn = map.get(remote, local);
            }
            map.remove(remote, local, conn);
        } finally {
            writeLock.unlock();
        }
        return conn;
    }
}
