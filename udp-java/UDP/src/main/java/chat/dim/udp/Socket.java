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
import java.net.*;
import java.util.*;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class Socket extends Thread {

    /*  Max count for caching packages
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Each UDP data package is limited to no more than 576 bytes, so set the
        MAX_CACHE_SPACES to about 2,000,000 means it would take up to 1GB memory
        for the caching.
     */
    public static int MAX_CACHE_SPACES = 1024 * 1024 * 2;

    /*  Buffer size for receiving package
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    public static int BUFFER_SIZE = 2048;

    public final SocketAddress localAddress;
    public final String host;
    public final int port;

    private final DatagramSocket socket;

    // connection delegate
    private WeakReference<ConnectionDelegate> delegateRef = null;

    // connections
    private final Set<Connection> connections = new LinkedHashSet<>();
    private final ReadWriteLock connectionLock = new ReentrantReadWriteLock();

    // received packages
    private final List<DatagramPacket> cargoes = new ArrayList<>();
    private final ReadWriteLock cargoLock = new ReentrantReadWriteLock();

    public Socket(SocketAddress address) throws SocketException {
        super();
        localAddress = address;

        InetSocketAddress inetSocketAddress = (InetSocketAddress) address;
        host = inetSocketAddress.getHostString();
        port = inetSocketAddress.getPort();

        socket = createSocket();
    }

    public Socket(String host, int port) throws SocketException {
        this(new InetSocketAddress(host, port));
    }

    public Socket(int port) throws SocketException {
        this(new InetSocketAddress(port));
    }

    public boolean isRunning() {
        return !socket.isClosed();
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

    public synchronized ConnectionDelegate getDelegate() {
        if (delegateRef == null) {
            return null;
        }
        return delegateRef.get();
    }

    public synchronized void setDelegate(ConnectionDelegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
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
        return removedConnections;
    }

    private Connection getConnection(ConnectionStatus status) {
        Connection connection = null;
        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection item;
            while (iterator.hasNext()) {
                item = iterator.next();
                if (status.equals(item.getStatus())) {
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
     *  Get any expired connection
     *
     * @return connection needs maintain
     */
    private Connection getExpiredConnection() {
        return getConnection(ConnectionStatus.Default);
    }

    /**
     *  Get any error connection
     *
     * @return connection maybe lost
     */
    private Connection getErrorConnection() {
        return getConnection(ConnectionStatus.Error);
    }

    //
    //  Connection Status
    //

    private void updateSentTime(SocketAddress remoteAddress) {
        Connection connection = null;
        ConnectionStatus oldStatus = null, newStatus = null;
        Date now = new Date();
        float timestamp = now.getTime() / 1000.0f;

        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection item;
            while (iterator.hasNext()) {
                item = iterator.next();
                if (remoteAddress.equals(item.remoteAddress)) {
                    // refresh time
                    oldStatus = item.getStatus(timestamp);
                    item.updateSentTime(timestamp);
                    newStatus = item.getStatus(timestamp);
                    connection = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }

        // callback
        ConnectionDelegate delegate = getDelegate();
        if (oldStatus != null && !oldStatus.equals(newStatus) && delegate != null) {
            // assert connection != null: "connection error: " + remoteAddress;
            delegate.onConnectionStatusChanged(connection, oldStatus, newStatus);
        }
    }

    private void updateReceivedTime(SocketAddress remoteAddress) {
        Connection connection = null;
        ConnectionStatus oldStatus = null, newStatus = null;
        Date now = new Date();
        float timestamp = now.getTime() / 1000.0f;

        Lock readLock = connectionLock.readLock();
        readLock.lock();
        try {
            Iterator<Connection> iterator = connections.iterator();
            Connection item;
            while (iterator.hasNext()) {
                item = iterator.next();
                if (remoteAddress.equals(item.remoteAddress)) {
                    // refresh time
                    oldStatus = item.getStatus(timestamp);
                    item.updateReceivedTime(timestamp);
                    newStatus = item.getStatus(timestamp);
                    connection = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }

        // callback
        ConnectionDelegate delegate = getDelegate();
        if (oldStatus != null && !oldStatus.equals(newStatus) && delegate != null) {
            // assert connection != null: "connection error: " + remoteAddress;
            delegate.onConnectionStatusChanged(connection, oldStatus, newStatus);
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
        Lock writeLock = cargoLock.writeLock();
        writeLock.lock();
        try {
            if (cargoes.size() > 0) {
                cargo = cargoes.remove(0);
            }
        } finally {
            writeLock.unlock();
        }
        return cargo;
    }

    private void cache(DatagramPacket cargo) {
        if (cargo.getOffset() > 0 || cargo.getLength() < cargo.getData().length) {
            // remove empty spaces
            byte[] buffer = new byte[cargo.getLength()];
            System.arraycopy(cargo.getData(), cargo.getOffset(), buffer, 0, cargo.getLength());
            cargo.setData(buffer);
        }
        Lock writeLock = cargoLock.writeLock();
        writeLock.lock();
        try {
            if (cargoes.size() >= MAX_CACHE_SPACES) {
                // drop the first package
                cargoes.remove(0);
            }
            // append the new package to the end
            cargoes.add(cargo);
        } finally {
            writeLock.unlock();
        }

        // callback
        ConnectionDelegate delegate = getDelegate();
        if (delegate != null) {
            Connection connection = getConnection(cargo.getSocketAddress());
            if (connection != null) {
                delegate.onConnectionReceivedData(connection);
            }
        }
    }

    @SuppressWarnings("SameParameterValue")
    private void _sleep(double seconds) {
        try {
            sleep((long) (seconds * 1000));
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
                packet = receive(BUFFER_SIZE);
                if (packet == null) {
                    // received nothing
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

    public void close() {
        socket.close();
    }

    /*
    public void stop() {
        // super.stop();
        close();
    }
     */
}
