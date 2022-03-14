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
package chat.dim.socket;

import java.io.IOException;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.ByteChannel;
import java.nio.channels.DatagramChannel;
import java.nio.channels.NetworkChannel;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SocketChannel;

import chat.dim.net.Channel;
import chat.dim.type.AddressPairObject;

public abstract class BaseChannel<C extends SelectableChannel>
        extends AddressPairObject
        implements Channel {

    // socket reader/writer
    protected final SocketReader reader;
    protected final SocketWriter writer;

    // inner socket
    private C impl;

    // flags
    private boolean blocking = false;
    private boolean opened = false;
    private boolean connected = false;
    private boolean bound = false;

    /**
     *  Create stream channel
     *
     * @param remote      - remote address
     * @param local       - local address
     */
    protected BaseChannel(SocketAddress remote, SocketAddress local, C sock) {
        super(remote, local);
        reader = createReader();
        writer = createWriter();
        impl = sock;
        refreshFlags();
    }

    @Override
    protected void finalize() throws Throwable {
        // make sure the relative socket is removed
        removeSocketChannel();
        super.finalize();
    }

    /**
     *  Create socket reader
     */
    protected abstract SocketReader createReader();

    /**
     *  Create socket writer
     */
    protected abstract SocketWriter createWriter();

    /**
     *  Refresh flags with inner socket
     */
    protected void refreshFlags() {
        C sock = impl;
        // update channel status
        if (sock == null) {
            blocking = false;
            opened = false;
            connected = false;
            bound = false;
        } else {
            blocking = sock.isBlocking();
            opened = sock.isOpen();
            connected = isConnected(sock);
            bound = isBound(sock);
        }
    }

    public C getSocketChannel() {
        return impl;
    }
    private void removeSocketChannel() throws IOException {
        // 1. clear inner channel
        C old = impl;
        impl = null;
        // 2. refresh flags
        refreshFlags();
        // 3. close old channel
        if (old != null && old.isOpen()) {
            old.close();
        }
    }

    private static boolean isConnected(SelectableChannel channel) {
        if (channel instanceof SocketChannel) {
            return ((SocketChannel) channel).isConnected();
        } else if (channel instanceof DatagramChannel) {
            return ((DatagramChannel) channel).isConnected();
        } else {
            return false;
        }
    }

    private static boolean isBound(SelectableChannel channel) {
        if (channel instanceof SocketChannel) {
            return ((SocketChannel) channel).socket().isBound();
        } else if (channel instanceof DatagramChannel) {
            return ((DatagramChannel) channel).socket().isBound();
        } else {
            return false;
        }
    }

    @Override
    public SelectableChannel configureBlocking(boolean block) throws IOException {
        C sock = getSocketChannel();
        if (sock == null) {
            throw new SocketException("socket closed");
        }
        sock.configureBlocking(block);
        blocking = block;
        return sock;
    }

    @Override
    public boolean isBlocking() {
        return blocking;
    }

    @Override
    public boolean isOpen() {
        return opened;
    }

    @Override
    public boolean isConnected() {
        return connected;
    }

    @Override
    public boolean isBound() {
        return bound;
    }

    @Override
    public boolean isAlive() {
        return isOpen() && (isConnected() || isBound());
    }

    @Override
    public NetworkChannel bind(SocketAddress local) throws IOException {
        if (local == null) {
            local = localAddress;
            assert local != null : "local address not set";
        }
        C sock = getSocketChannel();
        if (sock == null) {
            throw new SocketException("socket closed");
        }
        NetworkChannel nc = ((NetworkChannel) sock).bind(local);
        localAddress = local;
        bound = true;
        opened = true;
        blocking = sock.isBlocking();
        return nc;
    }

    @Override
    public NetworkChannel connect(SocketAddress remote) throws IOException {
        if (remote == null) {
            remote = remoteAddress;
            assert remote != null : "remote address not set";
        }
        C sock = getSocketChannel();
        if (sock == null) {
            throw new SocketException("socket closed");
        }
        if (sock instanceof SocketChannel) {
            ((SocketChannel) sock).connect(remote);
        } else if (sock instanceof DatagramChannel) {
            ((DatagramChannel) sock).connect(remote);
        } else {
            throw new SocketException("unknown datagram channel: " + sock);
        }
        remoteAddress = remote;
        connected = true;
        opened = true;
        blocking = sock.isBlocking();
        return (NetworkChannel) sock;
    }

    @Override
    public ByteChannel disconnect() throws IOException {
        C sock = getSocketChannel();
        if (sock instanceof DatagramChannel) {
            try {
                return ((DatagramChannel) sock).disconnect();
            } finally {
                refreshFlags();
            }
        } else {
            removeSocketChannel();
        }
        return sock instanceof ByteChannel ? (ByteChannel) sock : null;
    }

    @Override
    public void close() throws IOException {
        // close inner socket and refresh flags
        removeSocketChannel();
    }

    //
    //  Input/Output
    //

    @Override
    public int read(ByteBuffer dst) throws IOException {
        try {
            return reader.read(dst);
        } catch (IOException e) {
            close();
            throw e;
        }
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        try {
            return writer.write(src);
        } catch (IOException e) {
            close();
            throw e;
        }
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        try {
            return reader.receive(dst);
        } catch (IOException e) {
            close();
            throw e;
        }
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        try {
            return writer.send(src, target);
        } catch (IOException e) {
            close();
            throw e;
        }
    }
}
