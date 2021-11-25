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
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.ByteChannel;
import java.nio.channels.DatagramChannel;
import java.nio.channels.NetworkChannel;
import java.nio.channels.ReadableByteChannel;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SocketChannel;
import java.nio.channels.WritableByteChannel;

import chat.dim.type.AddressPairObject;

public abstract class BaseChannel<C extends SelectableChannel> extends AddressPairObject implements Channel {

    private C channel;

    // flags
    private boolean blocking = false;
    private boolean opened = false;
    private boolean connected = false;
    private boolean bound = false;

    /**
     *  Create stream channel
     *
     * @param sock        - socket/datagram channel
     * @param remote      - remote address
     * @param local       - local address
     */
    protected BaseChannel(C sock, SocketAddress remote, SocketAddress local) {
        super(remote, local);
        channel = sock;
        refreshFlags();
    }

    protected void refreshFlags() {
        // update channel status
        C impl = getChannel();
        if (impl == null) {
            blocking = false;
            opened = false;
            connected = false;
            bound = false;
        } else {
            blocking = impl.isBlocking();
            opened = impl.isOpen();
            connected = isConnected(impl);
            bound = isBound(impl);
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

    protected C getChannel() {
        return channel;
    }

    @Override
    public SelectableChannel configureBlocking(boolean block) throws IOException {
        C impl = getChannel();
        if (impl == null) {
            throw new SocketException("socket closed");
        }
        impl.configureBlocking(block);
        blocking = block;
        return impl;
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
        C impl = getChannel();
        if (impl == null) {
            throw new SocketException("socket closed");
        }
        NetworkChannel nc = ((NetworkChannel) impl).bind(local);
        localAddress = local;
        bound = true;
        opened = true;
        blocking = impl.isBlocking();
        return nc;
    }

    @Override
    public NetworkChannel connect(SocketAddress remote) throws IOException {
        C impl = getChannel();
        if (impl == null) {
            throw new SocketException("socket closed");
        }
        if (impl instanceof SocketChannel) {
            ((SocketChannel) impl).connect(remote);
        } else if (impl instanceof DatagramChannel) {
            ((DatagramChannel) impl).connect(remote);
        } else {
            throw new SocketException("unknown datagram channel: " + impl);
        }
        remoteAddress = remote;
        connected = true;
        opened = true;
        blocking = impl.isBlocking();
        return (NetworkChannel) impl;
    }

    @Override
    public ByteChannel disconnect() throws IOException {
        C impl = channel;
        close();
        return (ByteChannel) impl;
    }

    @Override
    public void close() throws IOException {
        C impl = channel;
        if (impl != null && impl.isOpen()) {
            impl.close();
        }
        channel = null;
        // update flags
        blocking = false;
        opened = false;
        connected = false;
        bound = false;
    }

    //
    //  Input/Output
    //

    @Override
    public int read(ByteBuffer dst) throws IOException {
        C impl = getChannel();
        if (impl instanceof ReadableByteChannel) {
            return ((ReadableByteChannel) impl).read(dst);
        } else {
            throw new SocketException("socket lost, cannot read data");
        }
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        C impl = getChannel();
        if (impl instanceof WritableByteChannel) {
            return ((WritableByteChannel) impl).write(src);
        } else {
            throw new SocketException("socket lost, cannot write data: " + src.position() + " byte(s)");
        }
    }
}
