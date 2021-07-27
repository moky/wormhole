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

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.ByteChannel;
import java.nio.channels.DatagramChannel;
import java.nio.channels.NetworkChannel;
import java.nio.channels.SelectableChannel;

import chat.dim.net.Channel;

public class DiscreteChannel implements Channel {

    protected DatagramChannel impl;
    private boolean blocking;
    private final boolean reuseAddress;

    public DiscreteChannel(DatagramChannel channel) throws IOException {
        super();
        impl = channel;
        blocking = channel.isBlocking();
        reuseAddress = channel.socket().getReuseAddress();
    }

    /**
     *  Create discrete channel
     *
     * @param remoteAddress - remote address
     * @param localAddress  - local address
     * @param nonBlocking   - whether blocking mode
     * @param reuse         - whether reuse address
     * @throws IOException on failed
     */
    public DiscreteChannel(SocketAddress remoteAddress, SocketAddress localAddress,
                           boolean nonBlocking, boolean reuse) throws IOException {
        super();
        blocking = !nonBlocking;
        reuseAddress = reuse;
        // create inner channel
        impl = DatagramChannel.open();
        impl.configureBlocking(blocking);
        impl.socket().setReuseAddress(reuseAddress);
        // bind to local address
        if (localAddress != null) {
            impl.bind(localAddress);
        }
        // connect to remote address
        if (remoteAddress != null) {
            impl.connect(remoteAddress);
        }
    }
    public DiscreteChannel(SocketAddress remoteAddress, SocketAddress localAddress) throws IOException {
        this(remoteAddress, localAddress, false, false);
    }

    private void setImpl() throws IOException {
        if (impl == null) {
            impl = DatagramChannel.open();
            impl.configureBlocking(blocking);
            impl.socket().setReuseAddress(reuseAddress);
        }
    }

    @Override
    public SelectableChannel configureBlocking(boolean block) throws IOException {
        blocking = block;
        if (impl == null) {
            setImpl();
        } else {
            impl.configureBlocking(block);
        }
        return impl;
    }

    @Override
    public boolean isBlocking() {
        return impl != null ? impl.isBlocking() : blocking;
    }

    @Override
    public boolean isOpen() {
        return impl != null && impl.isOpen();
    }

    @Override
    public boolean isConnected() {
        return impl != null && impl.isConnected();
    }

    @Override
    public boolean isBound() {
        return impl != null && impl.socket().isBound();
    }

    @Override
    public SocketAddress getLocalAddress() throws IOException {
        return impl == null ? null : impl.getLocalAddress();
    }

    @Override
    public SocketAddress getRemoteAddress() throws IOException {
        return impl == null ? null : impl.getRemoteAddress();
    }

    @Override
    public NetworkChannel bind(SocketAddress local) throws IOException {
        setImpl();
        return impl.bind(local);
    }

    @Override
    public NetworkChannel connect(SocketAddress remote) throws IOException {
        setImpl();
        return impl.connect(remote);
    }

    @Override
    public ByteChannel disconnect() throws IOException {
        ByteChannel sock = impl;
        close();
        return sock;
    }

    @Override
    public void close() throws IOException {
        if (impl != null && impl.isOpen()) {
            impl.close();
        }
        impl = null;
    }

    //
    //  Input/Output
    //

    @Override
    public int read(ByteBuffer dst) throws IOException {
        return impl.read(dst);
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        return impl.write(src);
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        if (impl.isConnected()) {
            return impl.read(dst) > 0 ? impl.getRemoteAddress() : null;
        } else {
            return impl.receive(dst);
        }
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        if (impl.isConnected()) {
            assert target == null || target.equals(impl.getRemoteAddress()) :
                    "target address error: " + target + ", " + impl.getRemoteAddress();
            return impl.write(src);
        } else {
            assert target != null : "target address missed for unbound channel";
            return impl.send(src, target);
        }
    }
}
