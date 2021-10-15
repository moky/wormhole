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

import chat.dim.net.ActiveConnection;
import chat.dim.net.Channel;
import chat.dim.net.Connection;

public class ClientHub extends StreamHub {

    public ClientHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Connection createConnection(Channel sock, SocketAddress remote, SocketAddress local) {
        ActiveConnection conn = new ActiveConnection(sock, remote, local);
        conn.setDelegate(getDelegate());
        conn.setHub(this);
        conn.start();  // start FSM
        return conn;
    }

    @Override
    public Channel getChannel(SocketAddress remote, SocketAddress local) {
        Channel channel = super.getChannel(remote, local);
        if (channel == null) {
            channel = createChannel(remote, local);
            if (channel != null) {
                putChannel(channel);
            }
        }
        return channel;
    }

    private Channel createChannel(SocketAddress remote, SocketAddress local) {
        SocketChannel sock;
        try {
            sock = createSocket(remote, local);
            if (local == null) {
                local = sock.getLocalAddress();
            }
        } catch (IOException e) {
            //e.printStackTrace();
            return null;
        }
        return new StreamChannel(sock, remote, local);
    }

    private static SocketChannel createSocket(SocketAddress remote, SocketAddress local) throws IOException {
        SocketChannel sock = SocketChannel.open();
        sock.configureBlocking(true);
        sock.socket().setReuseAddress(false);
        if (local != null) {
            sock.bind(local);
        }
        sock.connect(remote);
        sock.configureBlocking(false);
        return sock;
    }
}
