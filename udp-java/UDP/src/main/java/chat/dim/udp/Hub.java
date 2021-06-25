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

/**
 *  Topology:
 *
 *                          +---------------+
 *                          |      APP      |
 *                          +---------------+
 *                              |       A
 *                              |       |  (filter)
 *                              V       |
 *          +-----------------------------------------------+
 *          |                                               |
 *          |     +----------+     HUB     +----------+     |
 *          |     |  socket  |             |  socket  |     |
 *          +-----+----------+-------------+----------+-----+
 *                   |    A                   |  |  A
 *                   |    |    (channels)     |  |  |
 *                   |    |                   |  |  |
 *          ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
 *          ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
 *                   |    |                   |  |  |
 *                   V    |                   V  V  |
 */

public class Hub extends Thread implements ConnectionHandler {

    private boolean running = false;

    // sockets
    private final Set<Socket> sockets = new LinkedHashSet<>();
    private final ReadWriteLock socketLock = new ReentrantReadWriteLock();

    // listeners
    private final Set<WeakReference<HubListener>> listeners = new LinkedHashSet<>();
    private final ReadWriteLock listenerLock = new ReentrantReadWriteLock();

    public Hub() {
        super();
    }

    //
    //  Listeners
    //

    public void addListener(HubListener listener) {
        Lock writeLock = listenerLock.writeLock();
        writeLock.lock();
        try {
            listeners.add(new WeakReference<>(listener));
        } finally {
            writeLock.unlock();
        }
    }

    public boolean removeListener(HubListener listener) {
        int count = 0;
        Lock writeLock = listenerLock.writeLock();
        writeLock.lock();
        try {
            Iterator<WeakReference<HubListener>> iterator = listeners.iterator();
            HubListener item;
            while (iterator.hasNext()) {
                item = iterator.next().get();
                if (listener.equals(item)) {
                    iterator.remove();
                    count += 1;
                    // break;
                }
            }
        } finally {
            writeLock.unlock();
        }
        return count > 0;
    }

    //
    //  Sockets
    //

    private Socket anySocket() {
        // Get arbitrary socket
        Socket socket = null;
        Lock readLock = socketLock.readLock();
        readLock.lock();
        try {
            Iterator<Socket> iterator = sockets.iterator();
            if (iterator.hasNext()) {
                socket = iterator.next();
            }
        } finally {
            readLock.unlock();
        }
        return socket;
    }

    private Set<Socket> allSockets() {
        // Get all sockets
        Set<Socket> all = new LinkedHashSet<>();
        Lock readLock = socketLock.readLock();
        readLock.lock();
        try {
            all.addAll(sockets);
        } finally {
            readLock.unlock();
        }
        return all;
    }

    private Set<Socket> getSockets(int port) {
        // Get all sockets bond to this port
        Set<Socket> matchedSockets = new LinkedHashSet<>();
        Lock readLock = socketLock.readLock();
        readLock.lock();
        try {
            InetSocketAddress address;
            for (Socket item : sockets) {
                if (port == item.port) {
                    matchedSockets.add(item);
                }
            }
        } finally {
            readLock.unlock();
        }
        return matchedSockets;
    }

    private Socket getSocket(int port) {
        // Get arbitrary socket bond to this port
        Socket socket = null;
        assert port != 0 : "port should not be ZERO";
        Lock readLock = socketLock.readLock();
        readLock.lock();
        try {
            InetSocketAddress address;
            for (Socket item : sockets) {
                if (port == item.port) {
                    socket = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }
        return socket;
    }

    private Socket getSocket(SocketAddress address) {
        // Get the socket bond to this address (host, port)
        Socket socket = null;
        Lock readLock = socketLock.readLock();
        readLock.lock();
        try {
            for (Socket item : sockets) {
                if (address.equals(item.localAddress)) {
                    socket = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }
        return socket;
    }

    protected Socket createSocket(SocketAddress address) throws SocketException {
        Socket socket = new Socket(address);
        socket.setHandler(this);
        new Thread(socket).start();
        return socket;
    }

    /**
     *  Create a socket on this address (port)
     *
     * @param address - address contains IP & port
     * @return socket
     * @throws SocketException on failed
     */
    public Socket open(SocketAddress address) throws SocketException {
        Socket socket;
        Lock writeLock = socketLock.writeLock();
        writeLock.lock();
        try {
            socket = getSocket(address);
            if (socket == null) {
                socket = createSocket(address);
                sockets.add(socket);
            }
        } finally {
            writeLock.unlock();
        }
        return socket;
    }

    public Socket open(String host, int port) throws SocketException {
        return open(new InetSocketAddress(host, port));
    }

    public Socket open(int port) throws SocketException {
        // get any socket bond to this port
        Socket socket;
        Lock writeLock = socketLock.writeLock();
        writeLock.lock();
        try {
            socket = getSocket(port);
            if (socket == null) {
                socket = createSocket(new InetSocketAddress(port));
                sockets.add(socket);
            }
        } finally {
            writeLock.unlock();
        }
        return socket;
    }

    /**
     *  Remove the socket on this address
     *
     * @param address - address contains IP & port
     * @return false on not found
     */
    public Set<Socket> close(SocketAddress address) {
        Set<Socket> closedSockets = new LinkedHashSet<>();
        Lock writeLock = socketLock.writeLock();
        writeLock.lock();
        try {
            Socket socket;
            while (true) {
                socket = getSocket(address);
                if (socket == null) {
                    break;
                }
                socket.close();
                closedSockets.add(socket);
                sockets.remove(socket);
            }
        } finally {
            writeLock.unlock();
        }
        return closedSockets;
    }

    /**
     *  Remove all sockets on this port
     *
     * @param port -
     * @return false on not found
     */
    public Set<Socket> close(int port) {
        Set<Socket> closedSockets = new LinkedHashSet<>();
        Lock writeLock = socketLock.writeLock();
        writeLock.lock();
        try {
            Socket socket;
            while (true) {
                socket = getSocket(port);
                if (socket == null) {
                    break;
                }
                socket.close();
                closedSockets.add(socket);
                sockets.remove(socket);
            }
        } finally {
            writeLock.unlock();
        }
        return closedSockets;
    }

    @Override
    public void start() {
        if (isAlive()) {
            return;
        }
        running = true;
        super.start();
    }

    /*
    public void stop() {
        // super.stop();
        close();
    }
     */

    public void close() {
        Lock writeLock = socketLock.writeLock();
        writeLock.lock();
        try {
            running = false;
            // close all sockets
            Iterator<Socket> iterator = sockets.iterator();
            Socket socket;
            while (iterator.hasNext()) {
                socket = iterator.next();
                socket.close();
                iterator.remove();
            }
        } finally {
            writeLock.unlock();
        }
    }

    //
    //  Connections
    //

    public Connection getConnection(SocketAddress destination, SocketAddress source) {
        Socket socket = getSocket(source);
        if (socket == null) {
            return null;
        }
        return socket.getConnection(destination);
    }

    private static Set<Connection> getConnections(SocketAddress destination, Set<Socket> sockets) {
        // Get connections from these sockets
        Set<Connection> connections = new LinkedHashSet<>();
        Connection conn;
        for (Socket sock : sockets) {
            conn = sock.getConnection(destination);
            if (conn != null) {
                connections.add(conn);
            }
        }
        return connections;
    }

    public Set<Connection> getConnections(SocketAddress destination, int source) {
        return getConnections(destination, getSockets(source));
    }

    public Set<Connection> getConnections(SocketAddress destination) {
        return getConnections(destination, allSockets());
    }

    /**
     *  Connect to the destination address by the socket bond to this source address
     *
     * @param destination - remote IP and port
     * @param source      - local IP and port
     * @return connection
     */
    public Connection connect(SocketAddress destination, SocketAddress source) {
        Socket socket = getSocket(source);
        if (socket == null) {
            return null;
        }
        return socket.connect(destination);
    }

    /**
     *  Connect to the destination address by any socket bond to this source port
     *
     * @param destination - remote IP and port
     * @param source      - local port
     * @return connection
     */
    public Connection connect(SocketAddress destination, int source) {
        Socket socket = getSocket(source);
        if (socket == null) {
            return null;
        }
        return socket.connect(destination);
    }

    /**
     *  Connect to the destination address by any socket exists
     *
     * @param destination - remote IP and port
     * @return connection
     */
    public Connection connect(SocketAddress destination) {
        Socket socket = anySocket();
        if (socket == null) {
            return null;
        }
        return socket.connect(destination);
    }

    private static Set<Connection> disconnect(SocketAddress destination, Set<Socket> sockets) {
        Set<Connection> allConnections = new LinkedHashSet<>();
        Set<Connection> removedConnections;
        for (Socket sock : sockets) {
            removedConnections = sock.disconnect(destination);
            if (removedConnections.size() > 0) {
                allConnections.addAll(removedConnections);
            }
        }
        return allConnections;
    }

    /**
     *  Disconnect from the destination address by the socket bond to this source address
     *
     * @param destination - remote IP and port
     * @param source      - local IP and port
     * @return removed connections
     */
    public Set<Connection> disconnect(SocketAddress destination, SocketAddress source) {
        Socket socket = getSocket(source);
        if (socket == null) {
            return null;
        }
        return socket.disconnect(destination);
    }

    /**
     *  Disconnect from the destination address by all sockets bond to this source port
     *
     * @param destination - remote IP and port
     * @param source      - local port
     * @return removed connections
     */
    public Set<Connection> disconnect(SocketAddress destination, int source) {
        return disconnect(destination, getSockets(source));
    }

    /**
     *  Disconnect from the destination address by all sockets
     *
     * @param destination - remote IP and port
     * @return removed connections
     */
    public Set<Connection> disconnect(SocketAddress destination) {
        return disconnect(destination, allSockets());
    }

    //
    //  Send / Receive
    //

    /**
     *  Send data to the destination address by the socket bound to this source address
     *
     * @param data        - UDP data package
     * @param destination - remote IP and port
     * @param source      - local IP and port
     * @return how many bytes have been sent
     */
    public int send(byte[] data, SocketAddress destination, SocketAddress source) {
        Socket socket = getSocket(source);
        if (socket == null) {
            return -1;
        }
        return socket.send(data, destination);
    }

    /**
     *  Send data to the destination address by any socket bound to this source port
     *
     * @param data        - UDP data package
     * @param destination - remote IP and port
     * @param source      - local port
     * @return how many bytes have been sent
     */
    public int send(byte[] data, SocketAddress destination, int source) {
        Socket socket = getSocket(source);
        if (socket == null) {
            return -1;
        }
        return socket.send(data, destination);
    }

    /**
     *  Send data to the destination address by any socket exists
     *
     * @param data        - UDP data package
     * @param destination - remote IP and port
     * @return how many bytes have been sent
     */
    public int send(byte[] data, SocketAddress destination) {
        Socket socket = anySocket();
        if (socket == null) {
            return -1;
        }
        return socket.send(data, destination);
    }

    private static void _sleep(double seconds) {
        try {
            sleep((long) (seconds * 1000));
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    private static Cargo receivePacket(Set<Socket> sockets) {
        // Receive data from these given sockets
        Cargo cargo = null;
        DatagramPacket packet;
        for (Socket sock : sockets) {
            packet = sock.receive();
            if (packet != null) {
                // got one
                cargo = new Cargo(packet, sock);
                break;
            }
        }
        return cargo;
    }

    private static Cargo receivePacket(Set<Socket> sockets, float timeout) {
        // Block to receive data from these given sockets
        long now = (new Date()).getTime(); // milliseconds
        long expired = now + (long) (timeout * 1000);

        Cargo cargo = null;
        while (now <= expired) {
            cargo = receivePacket(sockets);
            if (cargo != null) {
                // got it
                break;
            }
            // receive nothing, have a rest for next job
            _sleep(0.1);
            now = (new Date()).getTime();
        }
        return cargo;
    }

    /**
     *  Block to receive data
     *
     * @param source  - local IP and port
     * @param timeout - timeout in seconds
     * @return cargo with data and addresses
     */
    public Cargo receive(SocketAddress source, float timeout) throws IOException {
        Socket sock = getSocket(source);
        if (sock == null) {
            throw new IOException("socket not found: " + source);
        }
        Set<Socket> sockets = new LinkedHashSet<>();
        sockets.add(sock);
        if (timeout < 0) {
            timeout = FOREVER;
        }
        return receivePacket(sockets, timeout);
    }

    public Cargo receive(int port, float timeout) {
        Set<Socket> sockets = getSockets(port);
        if (timeout < 0) {
            timeout = FOREVER;
        }
        return receivePacket(sockets, timeout);
    }

    public Cargo receive(float timeout) {
        Set<Socket> sockets = allSockets();
        if (timeout < 0) {
            timeout = FOREVER;
        }
        return receivePacket(sockets, timeout);
    }

    private static final long FOREVER = 31558150; // 3600 * 24 * 365.25636 (365d 6h 9m 10s)

    public Cargo receive(SocketAddress source) throws IOException {
        Socket sock = getSocket(source);
        if (sock == null) {
            throw new IOException("socket not found: " + source);
        }
        Set<Socket> sockets = new LinkedHashSet<>();
        sockets.add(sock);
        return receivePacket(sockets);
    }

    public Cargo receive(int port) throws IOException {
        Socket sock = getSocket(port);
        if (sock == null) {
            throw new IOException("socket not found: " + port);
        }
        Set<Socket> sockets = new LinkedHashSet<>();
        sockets.add(sock);
        return receivePacket(sockets);
    }

    public Cargo receive() throws IOException {
        Set<Socket> sockets = allSockets();
        if (sockets.size() == 0) {
            throw new IOException("socket not found");
        }
        return receivePacket(sockets);
    }

    @Override
    public void run() {
        long now = (new Date()).getTime();
        long expired = now + Connection.EXPIRES;
        Cargo cargo;
        List<byte[]> responses;

        while (running) {
            try {
                // try to receive data
                cargo = receivePacket(allSockets());
                if (cargo == null) {
                    // received nothing, have a rest
                    _sleep(0.1);
                } else {
                    // dispatch data and got responses
                    responses = dispatch(cargo.data, cargo.source, cargo.destination);
                    for (byte[] res : responses) {
                        send(res, cargo.source);
                    }
                }
                // check time for next heartbeat
                now = (new Date()).getTime();
                if (now > expired) {
                    heartbeat();
                    // try heartbeat for all connections in all sockets
                    expired = now + 2000;
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    protected void heartbeat() {
        Lock readLock = socketLock.readLock();
        readLock.lock();
        try {
            for (Socket socket : sockets) {
                socket.ping();  // try to keep all connections alive
                socket.purge(); // remove error connections
            }
        } finally {
            readLock.unlock();
        }
    }

    private List<byte[]> dispatch(byte[] data, SocketAddress source, SocketAddress destination) {
        List<byte[]> responses = new ArrayList<>();
        Lock readLock = listenerLock.readLock();
        readLock.lock();
        try {
            HubListener listener;
            HubFilter filter;
            byte[] res;
            for (WeakReference<HubListener> item : listeners) {
                listener = item.get();
                if (listener == null) {
                    // TODO: remove empty item
                    continue;
                }
                filter = listener.getFilter();
                if (filter != null && !filter.checkData(data, source, destination)) {
                    continue;
                }
                res = listener.onDataReceived(data, source, destination);
                if (res == null) {
                    continue;
                }
                responses.add(res);
            }
        } finally {
            readLock.unlock();
        }
        return responses;
    }

    //
    //  ConnectionHandler
    //

    @Override
    public void onConnectionStatusChanged(Connection connection, ConnectionStatus oldStatus, ConnectionStatus newStatus) {
        Lock readLock = listenerLock.readLock();
        readLock.lock();
        try {
            HubListener listener;
            HubFilter filter;
            for (WeakReference<HubListener> item : listeners) {
                listener = item.get();
                if (listener == null) {
                    // TODO: remove empty item
                    continue;
                }
                filter = listener.getFilter();
                if (filter != null && !filter.checkConnection(connection)) {
                    continue;
                }
                listener.onStatusChanged(connection, oldStatus, newStatus);
            }
        } finally {
            readLock.unlock();
        }
    }

    @Override
    public void onConnectionReceivedData(Connection connection) {
        /*
        if (running) {
            // process by run()
            return;
        }
        Cargo cargo = null;
        try {
            cargo = receive(connection.localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
        if (cargo == null) {
            // assert false : "receive error";
            return;
        }
        // dispatch data and got responses
        List<byte[]> responses = dispatch(cargo.data, cargo.source, cargo.destination);
        for (byte[] res : responses) {
            send(res, cargo.source);
        }
         */
    }
}
