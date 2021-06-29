/* license: https://mit-license.org
 *
 *  Star Gate: Network Connection Module
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
package chat.dim.network;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.Date;

import chat.dim.net.Channel;
import chat.dim.udp.DiscreteChannel;
import chat.dim.udp.PackageConnection;

public class StarGate extends PackageConnection {

    public static class Cargo {
        public final SocketAddress source;
        public final byte[] payload;
        public Cargo(SocketAddress remote, byte[] data) {
            source = remote;
            payload = data;
        }
    }

    public final DatagramChannel serverChannel;

    public StarGate(Channel byteChannel, DatagramChannel bindChannel) {
        super(byteChannel);
        serverChannel = bindChannel;
    }

    public static StarGate create(InetSocketAddress local) throws IOException {
        DiscreteChannel channel = new DiscreteChannel();
        channel.configureBlocking(true);
        DatagramChannel bind = (DatagramChannel) channel.bind(local);
        channel.configureBlocking(false);
        return new StarGate(channel, bind);
    }
    public static StarGate create(String host, int port) throws IOException {
        return create(new InetSocketAddress(host, port));
    }

    public int send(byte[] data, SocketAddress remote) {
        ByteBuffer buffer = ByteBuffer.allocate(data.length);
        buffer.put(data);
        buffer.flip();
        int sent;
        try {
            sent = serverChannel.send(buffer, remote);
        } catch (IOException e) {
            e.printStackTrace();
            return -1;
        }
        lastSentTime = (new Date()).getTime();
        return sent;
    }

    public Cargo recv() {
        ByteBuffer buffer = ByteBuffer.allocate(MTU);
        SocketAddress remote;
        try {
            remote = serverChannel.receive(buffer);
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
        int count = buffer.position();
        if (count <= 0) {
            return null;
        }
        byte[] data = new byte[count];
        buffer.flip();
        buffer.get(data);
        lastReceivedTime = (new Date()).getTime();
        return new Cargo(remote, data);
    }
}
