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
import java.nio.channels.ClosedChannelException;
import java.nio.channels.DatagramChannel;

import chat.dim.socket.BaseChannel;
import chat.dim.socket.ChannelReader;

public class PacketChannelReader extends ChannelReader<DatagramChannel> {

    protected PacketChannelReader(BaseChannel<DatagramChannel> channel) {
        super(channel);
    }

    //
    //  Receive
    //

    protected SocketAddress receiveFrom(ByteBuffer dst, DatagramChannel sock) throws IOException {
        SocketAddress remote = sock.receive(dst);
        int cnt = dst.position();
        if (cnt < 0) {
            // connection lost?
            throw new ClosedChannelException();
        }
        // OK
        return remote;
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        DatagramChannel sock = getSocket();
        assert sock != null : "socket lost, cannot receive data.";
        if (sock.isConnected()) {
            // connected (TCP/UDP)
            return read(dst) > 0 ? getRemoteAddress() : null;
        } else {
            // not connect (UDP)
            return receiveFrom(dst, sock);
        }
    }

}
