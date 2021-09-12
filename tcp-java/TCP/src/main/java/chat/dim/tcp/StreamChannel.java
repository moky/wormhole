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
import java.nio.channels.SocketChannel;

import chat.dim.net.BaseChannel;

public class StreamChannel extends BaseChannel<SocketChannel> {

    public StreamChannel(SocketChannel channel, SocketAddress remote, SocketAddress local) {
        super(channel, remote, local);
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        SocketChannel impl = getChannel();
        if (impl == null) {
            return null;
        }
        int res = impl.read(dst);
        if (res > 0) {
            return impl.getRemoteAddress();
        } else if (res < 0) {
            // channel closed by client
            close();
        }
        return null;
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        SocketChannel impl = getChannel();
        if (impl == null) {
            return -1;
        }
        assert target == null || target.equals(impl.getRemoteAddress()) :
                "target address error: " + target + ", " + impl.getRemoteAddress();
        return impl.write(src);
    }
}
