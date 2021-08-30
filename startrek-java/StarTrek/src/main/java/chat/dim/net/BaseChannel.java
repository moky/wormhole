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

public abstract class BaseChannel<C extends SelectableChannel> implements Channel {

    protected C channel;
    protected boolean blocking;
    protected final boolean reuseAddress;

    public BaseChannel(C channel, boolean blocking, boolean reuse) {
        super();
        this.channel = channel;
        this.blocking = blocking;
        this.reuseAddress = reuse;
    }

    /**
     *  Create stream channel
     *
     * @param remoteAddress - remote address
     * @param localAddress  - local address
     * @param nonBlocking   - whether blocking mode
     * @param reuse         - whether reuse address
     * @throws IOException on failed
     */
    public BaseChannel(SocketAddress remoteAddress, SocketAddress localAddress,
                         boolean nonBlocking, boolean reuse) throws IOException {
        super();
        blocking = !nonBlocking;
        reuseAddress = reuse;
        // setup inner channel
        channel = null;
        setupChannel();
        // bind to local address
        if (localAddress != null) {
            bind(localAddress);
        }
        // connect to remote address
        if (remoteAddress != null) {
            connect(remoteAddress);
        }
    }

    protected abstract C setupChannel() throws IOException;

    @Override
    public SelectableChannel configureBlocking(boolean block) throws IOException {
        blocking = block;
        C impl = channel;
        if (impl == null) {
            impl = setupChannel();
        } else {
            impl.configureBlocking(block);
        }
        return impl;
    }

    @Override
    public boolean isBlocking() {
        C impl = channel;
        return impl != null ? impl.isBlocking() : blocking;
    }

    @Override
    public boolean isOpen() {
        C impl = channel;
        return impl != null && impl.isOpen();
    }

    @Override
    public boolean isConnected() {
        C impl = channel;
        if (impl instanceof SocketChannel) {
            return ((SocketChannel) impl).isConnected();
        } else if (impl instanceof DatagramChannel) {
            return ((DatagramChannel) impl).isConnected();
        } else {
            return false;
        }
    }

    @Override
    public boolean isBound() {
        C impl = channel;
        if (impl instanceof SocketChannel) {
            return ((SocketChannel) impl).socket().isBound();
        } else if (impl instanceof DatagramChannel) {
            return ((DatagramChannel) impl).socket().isBound();
        } else {
            return false;
        }
    }

    @Override
    public SocketAddress getLocalAddress() throws IOException {
        C impl = channel;
        if (impl instanceof NetworkChannel) {
            return ((NetworkChannel) impl).getLocalAddress();
        } else {
            return null;
        }
    }

    @Override
    public SocketAddress getRemoteAddress() throws IOException {
        C impl = channel;
        if (impl instanceof SocketChannel) {
            return ((SocketChannel) impl).getRemoteAddress();
        } else if (impl instanceof DatagramChannel) {
            return ((DatagramChannel) impl).getRemoteAddress();
        } else {
            return null;
        }
    }

    @Override
    public NetworkChannel bind(SocketAddress local) throws IOException {
        C impl = setupChannel();
        return ((NetworkChannel) impl).bind(local);
    }

    @Override
    public NetworkChannel connect(SocketAddress remote) throws IOException {
        C impl = setupChannel();
        if (impl instanceof SocketChannel) {
            ((SocketChannel) impl).connect(remote);
        } else if (impl instanceof DatagramChannel) {
            ((DatagramChannel) impl).connect(remote);
        }
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
    }

    //
    //  Input/Output
    //

    @Override
    public int read(ByteBuffer dst) throws IOException {
        C impl = channel;
        if (impl instanceof ReadableByteChannel) {
            return ((ReadableByteChannel) impl).read(dst);
        } else {
            throw new SocketException("socket lost, cannot read data");
        }
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        C impl = channel;
        if (impl instanceof WritableByteChannel) {
            return ((WritableByteChannel) channel).write(src);
        } else {
            throw new SocketException("socket lost, cannot write data: " + src.position() + " byte(s)");
        }
    }
}
