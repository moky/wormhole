/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.udp;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

final class Socket implements Runnable {

    /*  Max count for caching packages
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     *
     *  Each UDP data package is limited to no more than 576 bytes, so set the
     *  MAX_CACHE_SPACES to about 2,000 means it would take up to 1MB memory
     *  for caching in one socket.
     */
    public static int MAX_CACHE_SPACES = 1024 * 2;

    /*  Maximum Transmission Unit
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     *
     *  Buffer size for receiving package
     */
    public static int MTU = 1472; // 1500 - 20 - 8

    public final InetSocketAddress localAddress;
    public final String host;
    public final int port;

    private final DatagramSocket socket;

    // connection handler
    private WeakReference<ConnectionHandler> handlerRef = null;

    // connections
    private final Set<Connection> connections = new LinkedHashSet<>();
    private final ReadWriteLock connectionLock = new ReentrantReadWriteLock();

    // declaration forms
    private final List<SocketAddress> declarations = new ArrayList<>();
    private final ReadWriteLock declarationLock = new ReentrantReadWriteLock();

    public Socket(InetSocketAddress address) throws SocketException {
        super();
        localAddress = address;

        host = address.getHostString();
        port = address.getPort();

        socket = createSocket();
    }

    protected DatagramSocket createSocket() throws SocketException {
        DatagramSocket socket = new DatagramSocket(localAddress);
        socket.setReuseAddress(true);
        socket.setSoTimeout(2);
        // socket.bind(localAddress);
        return socket;
    }

    public void setTimeout(int timeout) {
        try {
            socket.setSoTimeout(timeout);
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    public synchronized ConnectionHandler getHandler() {
        if (handlerRef == null) {
            return null;
        }
        return handlerRef.get();
    }

    public synchronized void setHandler(ConnectionHandler delegate) {
        if (delegate == null) {
            handlerRef = null;
        } else {
            handlerRef = new WeakReference<>(delegate);
        }
    }

    //
    //  Connections
    //

    public Connection getConnection(SocketAddress remoteAddress) {
        Connection connection = null;
        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection item;
            while (iterator.hasNext()) {
                item = iterator.next();
                if (remoteAddress.equals(item.remoteAddress)) {
                    // got it
                    connection = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }
        return connection;
    }

    protected Connection createConnection(SocketAddress remoteAddress, SocketAddress localAddress) {
        return new Connection(remoteAddress, localAddress);
    }

    /**
     *  Add remote address to keep connected with heartbeat
     *
     * @param remoteAddress - remote IP and port
     * @return connection
     */
    public Connection connect(SocketAddress remoteAddress) {
        Connection connection = null;
        Lock writeLock = connectionLock.writeLock();
        writeLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection item;
            while (iterator.hasNext()) {
                item = iterator.next();
                if (remoteAddress.equals(item.remoteAddress)) {
                    // already connected
                    connection = item;
                    break;
                }
            }
            if (connection == null) {
                connection = createConnection(remoteAddress, localAddress);
                connections.add(connection);
            }
        } finally {
            writeLock.unlock();
        }
        return connection;
    }

    /**
     *  Remove remote address from heartbeat tasks
     *
     * @param remoteAddress - remote IP and port
     * @return false on connection not found
     */
    @SuppressWarnings("UnusedReturnValue")
    public Set<Connection> disconnect(SocketAddress remoteAddress) {
        Set<Connection> removedConnections = new LinkedHashSet<>();
        Lock writeLock = connectionLock.writeLock();
        writeLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection conn;
            while (iterator.hasNext()) {
                conn = iterator.next();
                if (remoteAddress.equals(conn.remoteAddress)) {
                    // got one
                    removedConnections.add(conn);
                    iterator.remove();
                    // break;
                }
            }
        } finally {
            writeLock.unlock();
        }
        // clear declaration forms
        clearDeclarations(removedConnections);
        return removedConnections;
    }

    private void clearDeclarations(Set<Connection> removedConnections) {
        Lock writeLock = declarationLock.writeLock();
        writeLock.lock();
        try {
            for (Connection conn : removedConnections) {
                removeDeclarations(conn.remoteAddress);
            }
        } finally {
            writeLock.unlock();
        }
    }

    private void removeDeclarations(SocketAddress remoteAddress) {
        for (int index = declarations.size() - 1; index >= 0; --index) {
            if (remoteAddress.equals(declarations.get(index))) {
                declarations.remove(index);
            }
        }
    }

    /**
     *  Get any expired connection
     *
     * @return connection needs maintain
     */
    private Connection getExpiredConnection() {
        Connection connection = null;
        long now = (new Date()).getTime();

        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection item;
            while (iterator.hasNext()) {
                item = iterator.next();
                if (item.isExpired(now)) {
                    // got it
                    connection = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }
        return connection;
    }

    /**
     *  Get any error connection
     *
     * @return connection maybe lost
     */
    private Connection getErrorConnection() {
        Connection connection = null;
        long now = (new Date()).getTime();

        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection item;
            while (iterator.hasNext()) {
                item = iterator.next();
                if (item.isError(now)) {
                    // got it
                    connection = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }
        return connection;
    }

    //
    //  Connection Status
    //

    private void updateSentTime(SocketAddress remoteAddress) {
        Connection conn = getConnection(remoteAddress);
        if (conn == null) {
            return;
        }
        long now = (new Date()).getTime();
        // 1. get old status
        ConnectionStatus oldStatus = conn.getStatus(now);
        // 2. refresh time
        conn.updateSentTime(now);
        // 3. get new status
        ConnectionStatus newStatus = conn.getStatus(now);
        if (oldStatus.equals(newStatus)) {
            // status not changed
            return;
        }
        // callback
        ConnectionHandler delegate = getHandler();
        if (delegate != null) {
            delegate.onConnectionStatusChanged(conn, oldStatus, newStatus);
        }
    }

    private void updateReceivedTime(SocketAddress remoteAddress) {
        Connection conn = getConnection(remoteAddress);
        if (conn == null) {
            return;
        }
        long now = (new Date()).getTime();
        // 1. get old status
        ConnectionStatus oldStatus = conn.getStatus(now);
        // 2. refresh time
        conn.updateReceivedTime(now);
        // 3. get new status
        ConnectionStatus newStatus = conn.getStatus(now);
        if (oldStatus.equals(newStatus)) {
            // status not changed
            return;
        }
        // callback
        ConnectionHandler delegate = getHandler();
        if (delegate != null) {
            delegate.onConnectionStatusChanged(conn, oldStatus, newStatus);
        }
    }

    //
    //  Input/Output
    //

    /**
     *  Send data to remote address
     *
     * @param data - data bytes
     * @param remoteAddress - remote IP and port
     * @return how many bytes have been sent
     */
    @SuppressWarnings("UnusedReturnValue")
    public int send(byte[] data, SocketAddress remoteAddress) {
        int len = data.length;
        DatagramPacket packet = new DatagramPacket(data, 0, len, remoteAddress);
        try {
            socket.send(packet);
            updateSentTime(remoteAddress);
            return len;
        } catch (IOException e) {
            e.printStackTrace();
            return -1;
        }
    }

    private DatagramPacket receive(int bufferSize) {
        try {
            byte[] buffer = new byte[bufferSize];
            DatagramPacket packet = new DatagramPacket(buffer, bufferSize);
            // receive packet from socket
            socket.receive(packet);
            if (packet.getLength() > 0) {
                // refresh connection time
                updateReceivedTime(packet.getSocketAddress());
                return packet;
            }
            // received nothing (timeout?)
        } catch (IOException e) {
            // e.printStackTrace();
        }
        return null;
    }

    /**
     *  Get received data package from buffer, non-blocked
     *
     * @return received package with data and source address
     */
    public DatagramPacket receive() {
        DatagramPacket cargo = null;
        Lock writeLock = declarationLock.writeLock();
        writeLock.lock();
        try {
            SocketAddress remoteAddress;
            Connection conn;
            while (declarations.size() > 0) {
                // get first one
                remoteAddress = declarations.remove(0);
                conn = getConnection(remoteAddress);
                if (conn == null) {
                    // connection lost, remove all declaration forms with its socket address
                    removeDeclarations(remoteAddress);
                    continue;
                }
                cargo = conn.receive();
                if (cargo != null) {
                    // got one packet
                    break;
                }
            }
        } finally {
            writeLock.unlock();
        }
        return cargo;
    }

    private void cache(DatagramPacket cargo) {
        // 1. get connection by address in packet
        SocketAddress remoteAddress = cargo.getSocketAddress();
        Connection conn = getConnection(remoteAddress);
        if (conn == null) {
            /*  NOTICE:
             *      If received a package, not heartbeat (PING, PONG),
             *      create a connection for caching it.
             */
            conn = connect(remoteAddress);
        }

        Lock writeLock = declarationLock.writeLock();
        writeLock.lock();
        try {
            // 2. append packet to connection's cache
            DatagramPacket ejected = conn.cache(cargo);
            /*  NOTICE:
             *      If something ejected, means this connection's cache is full,
             *      don't append new form for it, just keep the old ones in queue,
             *      this will let the old forms have a higher priority
             *      to be processed as soon as possible.
             */
            if (ejected == null) {
                // append the new form to the end
                declarations.add(remoteAddress);
            }

            // 3. check socket memory cache
            if (isCacheFull(declarations.size(), remoteAddress)) {
                /*  NOTICE:
                 *      this socket is full, eject one cargo from any connection.
                 *      notice that the connection which cache is full will have
                 *      a higher priority to be ejected.
                 */
                receive();
            }
        } finally {
            writeLock.unlock();
        }

        // 4. callback
        ConnectionHandler delegate = getHandler();
        if (delegate != null) {
            delegate.onConnectionReceivedData(conn);
        }
    }

    protected boolean isCacheFull(int count, SocketAddress remoteAddress) {
        return count > MAX_CACHE_SPACES;
    }

    /*
    @Override
    public void start() {
        if (isAlive()) {
            return;
        }
        super.start();
    }
     */

    /*
    public void stop() {
        // super.stop();
        close();
    }
     */

    public void close() {
        // TODO: disconnect all connections (clear declaration forms)
        socket.close();
    }

    private boolean isRunning() {
        return !socket.isClosed();
    }

    @SuppressWarnings("SameParameterValue")
    private void _sleep(double seconds) {
        try {
            Thread.sleep((long) (seconds * 1000));
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void run() {
        DatagramPacket packet;
        byte[] data;
        while (isRunning()) {
            try {
                packet = receive(MTU);
                if (packet == null) {
                    // received nothing, have a rest
                    _sleep(0.1);
                    continue;
                }
                if (packet.getLength() == 4) {
                    // check heartbeat
                    data = packet.getData();
                    if (data[0] == 'P' && data[2] == 'N' && data[3] == 'G') {
                        if (data[1] == 'I') {
                            // got 'PING': respond heartbeat
                            send(PONG, packet.getSocketAddress());
                            continue;
                        } else if (data[1] == 'O') {
                            // got 'PONG': ignore it
                            continue;
                        }
                    }
                }
                // cache the data package received
                cache(packet);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private final byte[] PING = {'P', 'I', 'N', 'G'};
    private final byte[] PONG = {'P', 'O', 'N', 'G'};

    /**
     *  Send heartbeat to all expired connections
     */
    public int ping() {
        int count = 0;
        Connection connection;
        while (true) {
            connection = getExpiredConnection();
            if (connection == null) {
                // no more expired connection
                break;
            }
            send(PING, connection.remoteAddress);
            count += 1;
        }
        return count;
    }

    /**
     *  Remove error connections
     */
    public Set<Connection> purge() {
        Set<Connection> allConnections = new LinkedHashSet<>();
        Set<Connection> removedConnections;
        Connection connection;
        while (true) {
            connection = getErrorConnection();
            if (connection == null) {
                // no more error connection
                break;
            }
            // remove error connection (long time to receive nothing)
            removedConnections = disconnect(connection.remoteAddress);
            if (removedConnections.size() > 0) {
                allConnections.addAll(removedConnections);
            }
        }
        return allConnections;
    }
}
