/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
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
package chat.dim.tcp;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.ByteChannel;
import java.nio.channels.NetworkChannel;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SocketChannel;

import chat.dim.net.Channel;

public class StreamChannel implements Channel {

    protected SocketChannel impl;
    private boolean blocking;

    public StreamChannel(SocketChannel channel, boolean block) throws IOException {
        super();
        impl = channel;
        blocking = block;
        if (channel.isBlocking() != blocking) {
            channel.configureBlocking(blocking);
        }
    }

    public StreamChannel(SocketChannel channel) {
        super();
        impl = channel;
        blocking = channel.isBlocking();
    }

    public StreamChannel() {
        super();
        impl = null;
        blocking = false;
    }

    private void setImpl() throws IOException {
        if (impl == null) {
            impl = SocketChannel.open();
            impl.configureBlocking(blocking);
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
        return impl.connect(remote) ? impl : null;
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
        return impl.read(dst) > 0 ? impl.getRemoteAddress() : null;
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        return impl.write(src);
    }
}
