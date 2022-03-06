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

import chat.dim.net.BaseChannel;
import chat.dim.socket.ChannelReader;

public abstract class PackageChannelReader extends ChannelReader<DatagramChannel> {

    protected PackageChannelReader(BaseChannel<DatagramChannel> channel) {
        super(channel);
    }

    protected SocketAddress tryReceive(ByteBuffer dst, DatagramChannel sock) throws IOException {
        try {
            return sock.receive(dst);
        } catch (IOException e) {
            e = checkError(e, sock);
            if (e != null) {
                // connection lost?
                throw e;
            }
            // received nothing
            return null;
        }
    }

    protected SocketAddress receiveFrom(ByteBuffer dst, DatagramChannel sock) throws IOException {
        SocketAddress remote = tryReceive(dst, sock);
        int cnt = dst.position();
        // check data
        IOException error = checkData(dst, cnt, sock);
        if (error != null) {
            // connection lost!
            throw error;
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