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
import java.nio.channels.DatagramChannel;

import chat.dim.net.BaseChannel;

public class PackageChannel extends BaseChannel<DatagramChannel> {

    public PackageChannel(DatagramChannel channel) throws IOException {
        super(channel, channel.isBlocking(), channel.socket().getReuseAddress());
    }

    /**
     *  Create package channel
     *
     * @param remoteAddress - remote address
     * @param localAddress  - local address
     * @param nonBlocking   - whether blocking mode
     * @param reuse         - whether reuse address
     * @throws IOException on failed
     */
    public PackageChannel(SocketAddress remoteAddress, SocketAddress localAddress,
                           boolean nonBlocking, boolean reuse) throws IOException {
        super(remoteAddress, localAddress, nonBlocking, reuse);
    }
    public PackageChannel(SocketAddress remoteAddress, SocketAddress localAddress) throws IOException {
        this(remoteAddress, localAddress, false, false);
    }

    @Override
    protected DatagramChannel setupChannel() throws IOException {
        if (channel == null) {
            channel = DatagramChannel.open();
            channel.configureBlocking(blocking);
            channel.socket().setReuseAddress(reuseAddress);
        }
        return channel;
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        if (channel.isConnected()) {
            return channel.read(dst) > 0 ? channel.getRemoteAddress() : null;
        } else {
            return channel.receive(dst);
        }
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        if (channel.isConnected()) {
            assert target == null || target.equals(channel.getRemoteAddress()) :
                    "target address error: " + target + ", " + channel.getRemoteAddress();
            return channel.write(src);
        } else {
            assert target != null : "target address missed for unbound channel";
            return channel.send(src, target);
        }
    }
}
