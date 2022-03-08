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
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;

import chat.dim.net.BaseConnection;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.threading.Daemon;

public class ServerHub extends StreamHub implements Runnable {

    private SocketAddress localAddress = null;
    private ServerSocketChannel master = null;

    private final Daemon daemon;
    private boolean running;

    public ServerHub(Connection.Delegate delegate, boolean isDaemon) {
        super(delegate);
        daemon = new Daemon(this, isDaemon);
        running = false;
    }
    public ServerHub(Connection.Delegate delegate) {
        this(delegate, true);
    }

    @Override
    protected Connection createConnection(Channel sock, SocketAddress remote, SocketAddress local) {
        Connection.Delegate gate = getDelegate();
        BaseConnection conn = new BaseConnection(remote, local, sock, gate);
        conn.start();  // start FSM
        return conn;
    }

    public void bind(SocketAddress local) throws IOException {
        if (local == null) {
            local = localAddress;
            assert local != null : "local address not set";
        }
        ServerSocketChannel sock = ServerSocketChannel.open();
        sock.configureBlocking(true);
        sock.socket().setReuseAddress(true);
        sock.socket().bind(local);
        sock.configureBlocking(false);
        setMaster(sock);
        localAddress = local;
    }

    protected void setMaster(ServerSocketChannel channel) {
        // 1. replace with new channel
        ServerSocketChannel old = master;
        master = channel;
        // 2. close old channel
        if (old != null && old != channel) {
            if (old.isOpen()) {
                try {
                    old.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    public boolean isRunning() {
        return running;
    }

    public void start() {
        stop();
        running = true;
        daemon.start();
    }

    public void stop() {
        running = false;
        daemon.stop();
    }

    @Override
    public void run() {
        SocketChannel sock;
        running = true;
        while (isRunning()) {
            try {
                sock = master.accept();
                if (sock != null) {
                    accept(sock, sock.getRemoteAddress(), localAddress);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    // override for user-customized channel
    protected void accept(SocketChannel sock, SocketAddress remote, SocketAddress local) {
        Channel channel = createChannel(sock, remote, local);
        assert channel != null : "failed to create socket channel: " + sock + ", remote=" + remote + ", local=" + local;
        setChannel(channel.getRemoteAddress(), channel.getLocalAddress(), channel);
    }
}
