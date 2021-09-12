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
     * @return all channels
     */
    protected abstract Set<Channel> allChannels();

    @Override
    public void closeChannel(Channel channel) {
        if (channel == null || !channel.isOpen()) {
            return;
        }
        try {
            channel.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public Connection getConnection(SocketAddress remote, SocketAddress local) {
        return connectionPool.get(remote, local);
    }

    protected void setConnection(SocketAddress remote, SocketAddress local, Connection connection) {
        connectionPool.put(remote, local, connection);
    }

    @Override
    public void closeConnection(Connection connection) {
        SocketAddress remote = connection.getRemoteAddress();
        SocketAddress local = connection.getLocalAddress();
        Connection conn = connectionPool.remove(remote, local, connection);
        if (conn != null) {
            conn.close();
        }
    }

    @Override
    public boolean process() {
        int count = 0;
        // 1. drive all channels to receive data
        Set<Channel> channels = allChannels();
        for (Channel sock : channels) {
            if (sock.isOpen() && drive(sock)) {
                // received data from this socket channel
                count += 1;
            }
        }
        // 2. drive all connections to move on
        Set<Connection> connections = connectionPool.allValues();
        ConnectionState state;
        for (Connection conn : connections) {
            // drive connection to go on
            conn.tick();
            // check connection state
            state = conn.getState();
            if (state == null || state.equals(ConnectionState.ERROR)) {
                // connection lost
                closeConnection(conn);
            }
        }
        return count > 0;
    }

    protected boolean drive(Channel sock) {
        // try to receive
        buffer.clear();
        SocketAddress remote;
        try {
            remote = sock.receive(buffer);
        } catch (IOException e) {
            e.printStackTrace();
            // socket error, remove the channel
            closeChannel(sock);
            return false;
        }
        if (remote == null) {
            // received nothing
            return false;
        }
        // get connection for processing received data
        Connection conn = getConnection(remote, sock.getLocalAddress());
        if (conn != null) {
            byte[] data = new byte[buffer.position()];
            buffer.flip();
            buffer.get(data);
            conn.received(data);
        }
        return true;
    }
    private final ByteBuffer buffer = ByteBuffer.allocate(MSS);
}
