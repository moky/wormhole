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

    private final ReadWriteLock connectionLock = new ReentrantReadWriteLock();
    private final AddressPairMap<Connection> connectionMap = new AddressPairMap<>();

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
        Lock writeLock = connectionLock.writeLock();
        writeLock.lock();
        try {
            connections = connectionMap.allValues();
        } finally {
            writeLock.unlock();
        }
        return connections;
    }

    Connection get(SocketAddress remote, SocketAddress local, boolean create) throws IOException {
        assert local != null || remote != null : "both local & remote addresses are empty";
        Connection conn;
        if (create) {
            Lock writeLock = connectionLock.writeLock();
            writeLock.lock();
            try {
                conn = connectionMap.get(remote, local);
            } finally {
                writeLock.unlock();
            }
        } else {
            Lock readLock = connectionLock.readLock();
            readLock.lock();
            try {
                conn = connectionMap.get(remote, local);
                if (conn == null) {
                    conn = getHub().createConnection(remote, local);
                    if (conn != null) {
                        connectionMap.put(remote, local, conn);
                    }
                }
            } finally {
                readLock.unlock();
            }
        }
        return conn;
    }

    Connection remove(SocketAddress remote, SocketAddress local, Connection conn) {
        assert local != null || remote != null : "both local & remote addresses are empty";
        Lock writeLock = connectionLock.writeLock();
        writeLock.lock();
        try {
            if (conn == null) {
                conn = connectionMap.get(remote, local);
            }
            connectionMap.remove(remote, local, conn);
        } finally {
            writeLock.unlock();
        }
        return conn;
    }
}
