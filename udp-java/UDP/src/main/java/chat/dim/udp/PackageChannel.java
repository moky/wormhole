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
import java.nio.channels.ByteChannel;
import java.nio.channels.DatagramChannel;

import chat.dim.net.BaseChannel;

public abstract class PackageChannel extends BaseChannel<DatagramChannel> {

    private DatagramChannel channel;

    public PackageChannel(SocketAddress remote, SocketAddress local, DatagramChannel sock) {
        super(remote, local);
        channel = sock;
        refreshFlags(sock);
    }

    @Override
    public DatagramChannel getSocketChannel() {
        return channel;
    }

    @Override
    protected void setSocketChannel(DatagramChannel sock) throws IOException {
        // 1. replace with new channel
        DatagramChannel old = channel;
        channel = sock;
        // 2. refresh flags with new channel
        refreshFlags(sock);
        // 3. close old channel
        if (old != null && old != sock) {
            if (old.isOpen() && old.isConnected()) {
                // DON'T close bound socket
                old.close();
            }
        }
    }

    @Override
    public ByteChannel disconnect() throws IOException {
        // DON'T close bound socket channel
        if (isBound() && !isConnected()) {
            return null;
        }
        return super.disconnect();
    }

    @Override
    public void close() throws IOException {
        // DON'T close bound socket channel
        if (isBound() && !isConnected()) {
            return;
        }
        super.close();
    }
}
