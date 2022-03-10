/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.udp;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;

import chat.dim.socket.BaseChannel;
import chat.dim.socket.ChannelWriter;

public class PackageChannelWriter extends ChannelWriter<DatagramChannel> {

    protected PackageChannelWriter(BaseChannel<DatagramChannel> channel) {
        super(channel);
    }

    @Override
    public DatagramChannel getSocket() {
        return getChannel().getSocketChannel();
    }

    @Override
    protected IOException checkError(IOException error, DatagramChannel sock) {
        // TODO: check 'E_AGAIN' & TimeoutException
        return error;
    }

    //
    //  Send
    //

    protected int trySend(ByteBuffer src, SocketAddress target, DatagramChannel sock) throws IOException {
        try {
            return sock.send(src, target);
        } catch (IOException e) {
            e = checkError(e, sock);
            if (e != null) {
                // connection lost?
                throw e;
            }
            // buffer overflow!
            return -1;
        }
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        DatagramChannel sock = getSocket();
        assert sock != null : "socket lost, cannot send data: " + src.position() + " byte(s)";
        if (sock.isConnected()) {
            // connected (TCP/UDP)
            assert target == null || target.equals(getRemoteAddress()) :
                    "target address error: " + target + ", " + getRemoteAddress();
            return tryWrite(src, sock);
        } else {
            // not connect (UDP)
            assert target != null : "target address missed for unbound channel";
            return trySend(src, target, sock);
        }
    }
}
