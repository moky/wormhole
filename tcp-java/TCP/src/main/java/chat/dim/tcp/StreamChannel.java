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
import java.nio.channels.SocketChannel;

import chat.dim.socket.BaseChannel;

public abstract class StreamChannel extends BaseChannel<SocketChannel> {

    private SocketChannel channel;

    public StreamChannel(SocketAddress remote, SocketAddress local, SocketChannel sock) {
        super(remote, local);
        channel = sock;
        refreshFlags(sock);
    }

    @Override
    public SocketChannel getSocketChannel() {
        return channel;
    }

    @Override
    protected void setSocketChannel(SocketChannel sock) throws IOException {
        // 1. replace with new socket
        SocketChannel old = channel;
        channel = sock;
        // 2. refresh flags with new socket
        refreshFlags(sock);
        // 3. close old socket
        if (old != null && old != sock) {
            if (old.isOpen()) {
                old.close();
            }
        }
    }
}
