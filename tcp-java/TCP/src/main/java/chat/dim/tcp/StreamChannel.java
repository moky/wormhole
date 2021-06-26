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

import chat.dim.net.Channel;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.ByteChannel;
import java.nio.channels.NetworkChannel;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SocketChannel;

public class StreamChannel implements Channel {

    private final SocketChannel impl;

    public StreamChannel() throws IOException {
        super();
        impl = SocketChannel.open();
    }

    @Override
    public SelectableChannel configureBlocking(boolean block) throws IOException {
        return impl.configureBlocking(block);
    }

    @Override
    public boolean isBlocking() {
        return impl.isBlocking();
    }

    @Override
    public boolean isBound() {
        return impl.isConnected();
    }

    @Override
    public boolean isClosed() {
        return !impl.isOpen();
    }

    @Override
    public NetworkChannel bind(SocketAddress local) throws IOException {
        return impl.bind(local);
    }

    @Override
    public SocketAddress getLocalAddress() throws IOException {
        return impl.getLocalAddress();
    }

    @Override
    public boolean isConnected() {
        return impl.isConnected();
    }

    @Override
    public boolean connect(SocketAddress remote) throws IOException {
        return impl.connect(remote);
    }

    @Override
    public SocketAddress getRemoteAddress() throws IOException {
        return impl.getRemoteAddress();
    }

    @Override
    public ByteChannel disconnect() throws IOException {
        impl.close();
        return this;
    }

    @Override
    public int read(ByteBuffer dst) throws IOException {
        return impl.read(dst);
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        return impl.write(src);
    }

    @Override
    public boolean isOpen() {
        return impl.isOpen();
    }

    @Override
    public void close() throws IOException {
        impl.close();
    }
}
