/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2022 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2022 Albert Moky
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
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.nio.channels.WritableByteChannel;

import chat.dim.socket.BaseChannel;
import chat.dim.socket.ChannelController;
import chat.dim.socket.SocketWriter;

public class StreamChannelWriter extends ChannelController<SocketChannel> implements SocketWriter {

    public StreamChannelWriter(BaseChannel<SocketChannel> channel) {
        super(channel);
    }

    // TODO: override for sending
    protected int sendAll(WritableByteChannel sock, ByteBuffer src) throws IOException {
        int sent = 0;
        int rest = src.position();
        int cnt;
        while (true) {  // while (sock.isOpen())
            cnt = sock.write(src);
            // check send result
            if (cnt <= 0) {
                // buffer overflow?
                break;
            }
            // something sent, check remaining data
            sent += cnt;
            rest -= cnt;
            if (rest <= 0) {
                // done!
                break;
                //} else {
                //    // remove sent part
            }
        }
        // OK
        if (sent > 0) {
            return sent;
        } else  if (cnt < 0) {
            assert cnt == -1 : "sent error: " + cnt;
            return -1;
        } else {
            return  0;
        }
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        SocketChannel sock = getSocket();
        if (sock == null || !sock.isOpen()) {
            throw new SocketException();
        }
        return sendAll(sock, src);
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        SocketChannel sock = getSocket();
        if (sock == null || !sock.isOpen()) {
            throw new SocketException();
        }
        // TCP channel will be always connected
        // so the target address must be the remote address
        SocketAddress remote = getRemoteAddress();
        assert target == null || target.equals(remote) : "target error: " + target + ", remote=" + remote;
        return write(src);
    }

}
