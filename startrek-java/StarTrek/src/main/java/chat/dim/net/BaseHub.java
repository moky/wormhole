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
import java.net.SocketAddress;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import chat.dim.type.AddressPairMap;
import chat.dim.type.Pair;

public abstract class BaseHub implements Hub {

    private final ConnectionPool connectionPool;

    // mapping: (remote, local) => time to kill
    private final Map<Pair<SocketAddress, SocketAddress>, Long> dyingTimes = new HashMap<>();
    public static long DYING_EXPIRES = 120 * 1000;

    protected BaseHub() {
        super();
        connectionPool = new ConnectionPool(this);
    }

    @Override
    public boolean send(byte[] data, SocketAddress source, SocketAddress destination) throws IOException {
        Connection conn = connect(destination, source);
        if (conn == null || !conn.isOpen()) {
            // connection closed
            return false;
        }
        return conn.send(data, destination) != -1;
    }

    protected abstract Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException;

    @Override
    public Connection getConnection(SocketAddress remote, SocketAddress local) {
        try {
            return connectionPool.get(remote, local, false);
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    @Override
    public Connection connect(SocketAddress remote, SocketAddress local) throws IOException {
        return connectionPool.get(remote, local, true);
    }

    @Override
    public void disconnect(SocketAddress remote, SocketAddress local) {
        assert local != null || remote != null : "both local & remote addresses are empty";
        Connection conn = connectionPool.remove(remote, local, null);
        if (conn != null) {
            conn.close();
        }
    }

    @Override
    public boolean process() {
        int activatedCount = 0;

        SocketAddress remote, local;
        Pair<SocketAddress, SocketAddress> aPair;  // (remote, local)
        long now = (new Date()).getTime();
        Long expired;
        Set<Connection> connections = connectionPool.all();
        for (Connection conn : connections) {
            // drive all connections to process
            if (conn.process()) {
                ++activatedCount;
            }
            // check closed connection(s)
            remote = conn.getRemoteAddress();
            local = conn.getLocalAddress();
            aPair = buildPair(remote, local);
            assert aPair != null : "connection error: " + conn;
            if (conn.isOpen()) {
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
                    connectionPool.remove(remote, local, conn);
                    // clear the death clock for it
                    dyingTimes.remove(aPair);
                }
            }
        }

        return activatedCount > 0;
    }
    private Pair<SocketAddress, SocketAddress> buildPair(SocketAddress remote, SocketAddress local) {
        if (remote == null) {
            if (local == null) {
                //throw new NullPointerException("both local & remote addresses are empty");
                return null;
            }
            return new Pair<>(AddressPairMap.AnyAddress, local);
        } else if (local == null) {
            return new Pair<>(remote, AddressPairMap.AnyAddress);
        } else {
            return new Pair<>(remote, local);
        }
    }
}
