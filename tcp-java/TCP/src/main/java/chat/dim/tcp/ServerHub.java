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
import java.net.SocketException;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.Map;
import java.util.WeakHashMap;

import chat.dim.net.BaseConnection;
import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;

public class ServerHub extends BaseHub implements Runnable {

    private final Map<SocketAddress, SocketChannel> slaves = new WeakHashMap<>();
    private SocketAddress localAddress = null;
    private ServerSocketChannel master = null;
    private boolean running = false;

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    public void bind(SocketAddress local) throws IOException {
        ServerSocketChannel sock = master;
        if (sock != null && sock.isOpen()) {
            sock.close();
        }
        sock = ServerSocketChannel.open();
        sock.socket().bind(local);
        //sock.configureBlocking(false);
        master = sock;
        localAddress = local;
    }

    public void start() {
        running = true;
        new Thread(this).start();
    }

    @Override
    public void run() {
        SocketChannel channel;
        SocketAddress remote;
        while (running) {
            try {
                channel = master.accept();
                System.out.println("new channel: " + channel);
                if (channel != null) {
                    remote = channel.getRemoteAddress();
                    slaves.put(remote, channel);
                    connect(remote, localAddress);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException {
        // create connection with channel
        BaseConnection conn = new BaseConnection(createChannel(remote, local), remote, local);
        // set delegate
        if (conn.getDelegate() == null) {
            conn.setDelegate(getDelegate());
        }
        // start FSM
        conn.start();
        return conn;
    }

    private Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        SocketChannel sock = slaves.get(remote);
        if (sock == null) {
            throw new SocketException("failed to get channel: " + remote + " -> " + local);
        } else {
            return new StreamChannel(sock);
        }
    }
}