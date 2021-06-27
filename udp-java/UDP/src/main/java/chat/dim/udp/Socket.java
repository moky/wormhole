/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.udp;

import java.io.Closeable;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;

public class Socket implements Closeable {

    /*  Maximum Transmission Unit
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     *
     *  Buffer size for receiving package
     */
    public static int MTU = 1472; // 1500 - 20 - 8

    /**
     *  Various states for this socket.
     */
    private boolean created = false;
    private boolean bound = false;
    private boolean connected = false;
    private boolean closed = false;
    private final Object closeLock = new Object();

    /**
     *  The implementation of this Socket
     */
    private DatagramChannel impl;

    void setImpl() throws IOException {
        impl = DatagramChannel.open();
        created = true;
    }

    /**
     *  Create an unconnected socket
     *
     * @throws IOException -
     */
    public Socket() throws IOException {
        super();
        setImpl();
    }

    /**
     *  Create an unconnected Socket with a user-specified DatagramChannel
     *
     * @param impl - an instance of a DatagramChannel the subclass wishes to use on the Socket
     */
    public Socket(DatagramChannel impl) {
        super();
        this.impl = impl;
    }

    private Socket(SocketAddress remote, SocketAddress local) throws IOException {
        // backward compatibility
        assert remote != null : "remote address empty";
        setImpl();
        try {
            if (local != null) {
                impl.bind(local);
            }
            impl.connect(remote);
        } catch (IOException e) {
            try {
                impl.close();
            } catch (IOException ce) {
                e.addSuppressed(ce);
            }
            throw e;
        }
    }

    /**
     *  Creates a socket and connects it to the specified port number on the named host.
     *  If the specified host is null it is the equivalent of specifying the address as InetAddress.getByName(null).
     *  In other words, it is equivalent to specifying an address of the loopback interface.
     *
     * @param host - the host name, or null for the loopback address.
     * @param port - the port number
     * @throws IOException - if an I/O error occurs when creating the socket.
     */
    public Socket(String host, int port) throws IOException {
        this(host != null ? new InetSocketAddress(host, port) :
                new InetSocketAddress(InetAddress.getByName(null), port), null);
    }

    /**
     *  Creates a socket and connects it to the specified port number at the specified IP address.
     *
     * @param address - the IP address
     * @param port    - the port number
     * @throws IOException - if an I/O error occurs when creating the socket.
     */
    public Socket(InetAddress address, int port) throws IOException {
        this(address != null ? new InetSocketAddress(address, port) : null, null);
    }

    /**
     *  Creates a socket and connects it to the specified remote host on the specified remote port.
     *  The Socket will also bind() to the local address and port supplied.
     *  If the specified host is null it is the equivalent of specifying the address as InetAddress.getByName(null).
     *  In other words, it is equivalent to specifying an address of the loopback interface.
     *  A local port number of zero will let the system pick up a free port in the bind operation.
     *
     * @param host         - the name of the remote host, or null for the loopback address.
     * @param port         - the remote port
     * @param localAddress - the local address the socket is bound to, or null for the anyLocal address.
     * @param localPort    - the local port the socket is bound to, or zero for a system selected free port.
     * @throws IOException - if an I/O error occurs when creating the socket.
     */
    public Socket(String host, int port, InetAddress localAddress, int localPort) throws IOException {
        this(host != null ? new InetSocketAddress(host, port) :
                new InetSocketAddress(InetAddress.getByName(null), port),
                new InetSocketAddress(localAddress, localPort));
    }

    /**
     *  Creates a socket and connects it to the specified remote address on the specified remote port.
     *  The Socket will also bind() to the local address and port supplied.
     *  If the specified local address is null it is the equivalent of specifying the address as the AnyLocal address
     *  (see InetAddress.isAnyLocalAddress()).
     *  A local port number of zero will let the system pick up a free port in the bind operation.
     *
     * @param address      - the remote address
     * @param port         - the remote port
     * @param localAddress - the local address the socket is bound to, or null for the anyLocal address.
     * @param localPort    - the local port the socket is bound to or zero for a system selected free port.
     * @throws IOException - if an I/O error occurs when creating the socket.
     */
    public Socket(InetAddress address, int port, InetAddress localAddress, int localPort) throws IOException {
        this(address != null ? new InetSocketAddress(address, port) : null,
                new InetSocketAddress(localAddress, localPort));
    }

    /**
     *  Connects this socket to the server with a specified timeout value.
     *  The connection will then block until established or an error occurs.
     *
     * @param remote - the SocketAddress
     * @throws IOException - if an error occurs during the connection
     */
    public void connect(InetSocketAddress remote) throws IOException {
        if (remote == null) {
            throw new IllegalArgumentException("connect: The address can't be null");
        } else if (isClosed()) {
            throw new SocketException("Socket is closed");
        } else if (isConnected()) {
            throw new SocketException("Already connected");
        }
        impl.connect(remote);
        connected = true;
        /*
         * If the socket was not bound before the connect, it is now because
         * the kernel will have picked an ephemeral port & a local address
         */
        bound = true;
    }

    /**
     *  Binds the socket to a local address.
     *  If the address is null, then the system will pick up an ephemeral port
     *  and a valid local address to bind the socket.
     *
     * @param local - the SocketAddress to bind to
     * @throws IOException if the bind operation fails, or if the socket is already bound.
     */
    public void bind(InetSocketAddress local) throws IOException {
        if (isClosed()) {
            throw new SocketException("Socket is closed");
        } else if (isBound()) {
            throw new SocketException("Already bound");
        } else if (local == null) {
            local = new InetSocketAddress(0);
        } else if (local.isUnresolved()) {
            throw new SocketException("Unresolved address: " + local);
        }
        impl.bind(local);
        bound = true;
    }

    /**
     *  Returns the address to which the socket is connected.
     *  If the socket was connected prior to being closed,
     *  then this method will continue to return the connected address after the socket is closed.
     *
     * @return the remote IP address to which this socket is connected, or null if the socket is not connected.
     */
    public InetAddress getInetAddress() {
        SocketAddress address = getRemoteSocketAddress();
        return address == null ? null : ((InetSocketAddress) address).getAddress();
    }

    /**
     *  Returns the remote port number to which this socket is connected.
     *  If the socket was connected prior to being closed,
     *  then this method will continue to return the connected port number after the socket is closed.
     *
     * @return the remote port number to which this socket is connected,
     *         or 0 if the socket is not connected yet.
     */
    public int getPort() {
        SocketAddress address = getRemoteSocketAddress();
        return address == null ? 0 : ((InetSocketAddress) address).getPort();
    }

    /**
     *  Gets the local address to which the socket is bound.
     *
     * @return the local address to which the socket is bound,
     *         the loopback address if denied by the security manager,
     *         or the wildcard address if the socket is closed or not bound yet.
     */
    public InetAddress getLocalAddress() {
        SocketAddress address = getLocalSocketAddress();
        return address == null ? null : ((InetSocketAddress) address).getAddress();
    }

    /**
     *  Returns the local port number to which this socket is bound.
     *  If the socket was bound prior to being closed,
     *  then this method will continue to return the local port number after the socket is closed.
     *
     * @return the local port number to which this socket is bound
     *         or -1 if the socket is not bound yet.
     */
    public int getLocalPort() {
        SocketAddress address = getLocalSocketAddress();
        return address == null ? -1 : ((InetSocketAddress) address).getPort();
    }

    /**
     *  Returns the address of the endpoint this socket is connected to, or null if it is unconnected.
     *  If the socket was connected prior to being closed,
     *  then this method will continue to return the connected address after the socket is closed.
     *
     * @return a SocketAddress representing the remote endpoint of this socket,
     *         or null if it is not connected yet.
     */
    public SocketAddress getRemoteSocketAddress() {
        if (!isConnected()) {
            return null;
        }
        try {
            return impl.getRemoteAddress();
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     *  Returns the address of the endpoint this socket is bound to.
     *  If a socket bound to an endpoint represented by an InetSocketAddress is closed,
     *  then this method will continue to return an InetSocketAddress after the socket is closed.
     *  In that case the returned InetSocketAddress's address is the wildcard address
     *  and its port is the local port that it was bound to.
     *
     * @return a SocketAddress representing the local endpoint of this socket,
     *         or null if the socket is not bound yet.
     */
    public SocketAddress getLocalSocketAddress() {
        if (!isBound()) {
            return null;
        }
        try {
            return impl.getLocalAddress();
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    //
    //  Input/Output
    //

    public int send(byte[] data) throws IOException {
        if (!isConnected()) {
            throw new SocketException("Socket not connect yet");
        }
        ByteBuffer buffer = ByteBuffer.allocate(data.length);
        buffer.put(data);
        buffer.flip();
        return impl.write(buffer);
    }

    public byte[] receive() throws IOException {
        ByteBuffer buffer = ByteBuffer.allocate(MTU);
        int res = impl.read(buffer);
        if (res <= 0) {
            return null;
        }
        assert res == buffer.position() : "buffer error: " + res + ", " + buffer.position();
        byte[] data = new byte[res];
        buffer.flip();
        buffer.get(data);
        return data;
    }

    /**
     *  Closes this socket.
     *  Any thread currently blocked in an I/O operation upon this socket will throw a SocketException.
     *  Once a socket has been closed, it is not available for further networking use
     *  (i.e. can't be reconnected or rebound). A new socket needs to be created.
     *
     * @throws IOException - if an I/O error occurs when closing this socket.
     */
    public void close() throws IOException {
        synchronized (closeLock) {
            if (isClosed()) {
                return;
            }
            if (created) {
                impl.close();
            }
            closed = true;
        }
    }

    @Override
    public String toString() {
        if (isConnected()) {
            return "Socket[address=" + getInetAddress() +
                    ", port=" + getPort() +
                    ", local port=" + getLocalPort() + "]";
        } else {
            return "Socket[unconnected]";
        }
    }

    /**
     *  Returns the connection state of the socket.
     *  Note: Closing a socket doesn't clear its connection state,
     *  which means this method will return true for a closed socket (see isClosed())
     *  if it was successfully connected prior to being closed.
     *
     * @return true if the socket was successfully connected to a server
     */
    public boolean isConnected() {
        return connected;
    }

    /**
     *  Returns the binding state of the socket.
     *  Note: Closing a socket doesn't clear its binding state,
     *  which means this method will return true for a closed socket (see isClosed())
     *  if it was successfully bound prior to being closed.
     *
     * @return true if the socket was successfully bound to an address
     */
    public boolean isBound() {
        return bound;
    }

    /**
     *  Returns the closed state of the socket.
     *
     * @return true if the socket has been closed
     */
    public boolean isClosed() {
        synchronized (closeLock) {
            return closed;
        }
    }
}
