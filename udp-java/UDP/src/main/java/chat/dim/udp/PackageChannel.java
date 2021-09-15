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
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;

import chat.dim.net.BaseChannel;

public class PackageChannel extends BaseChannel<DatagramChannel> {

    public PackageChannel(DatagramChannel channel, SocketAddress remote, SocketAddress local) {
        super(channel, remote, local);
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        DatagramChannel impl = getChannel();
        if (impl == null) {
            throw new SocketException("socket channel lost");
        }
        if (impl.isConnected()) {
            return impl.read(dst) > 0 ? getRemoteAddress() : null;
        } else {
            return impl.receive(dst);
        }
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        DatagramChannel impl = getChannel();
        if (impl == null) {
            throw new SocketException("socket channel lost");
        }
        if (impl.isConnected()) {
            assert target == null || target.equals(getRemoteAddress()) :
                    "target address error: " + target + ", " + getRemoteAddress();
            return impl.write(src);
        } else {
            assert target != null : "target address missed for unbound channel";
            return impl.send(src, target);
        }
    }
}
