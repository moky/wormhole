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

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.skywalker.Runner;
import chat.dim.socket.BaseChannel;
import chat.dim.socket.BaseConnection;
import chat.dim.threading.Daemon;

/**
 *  Stream Server Hub
 *  ~~~~~~~~~~~~~~~~~
 */
public class ServerHub extends StreamHub implements Runnable {

    private SocketAddress localAddress = null;
    private ServerSocketChannel master = null;

    private final Daemon daemon;
    private boolean running;

    public ServerHub(Connection.Delegate gate, boolean isDaemon) {
        super(gate);
        daemon = new Daemon(this, isDaemon);
        running = false;
    }
    public ServerHub(Connection.Delegate gate) {
        this(gate, true);
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        BaseConnection conn = new BaseConnection(remote, local);
        conn.setDelegate(getDelegate());  // gate
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

    protected ServerSocketChannel getMaster() {
        return master;
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

    public SocketAddress getLocalAddress() {
        return localAddress;
    }

    //
    //  Threading
    //

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
        Runner.sleep(256);
        daemon.stop();
    }

    @Override
    public void run() {
        ServerSocketChannel srv;
        SocketChannel sock;
        running = true;
        while (isRunning()) {
            srv = getMaster();
            if (srv == null) {
                assert false : "master socket not found";
                break;
            }
            try {
                sock = srv.accept();
                if (sock == null) {
                    Runner.sleep(Runner.INTERVAL_NORMAL);
                } else {
                    accept(sock.getRemoteAddress(), getLocalAddress(), sock);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    // override for user-customized channel
    @SuppressWarnings("unchecked")
    protected void accept(SocketAddress remote, SocketAddress local, SocketChannel sock) {
        // create new channel
        Channel channel = createChannel(remote, local);
        if (local == null) {
            local = channel.getLocalAddress();
        }
        try {
            sock.configureBlocking(false);
        } catch (IOException e) {
            e.printStackTrace();
        }
        // set socket
        if (channel instanceof BaseChannel) {
            ((BaseChannel<SocketChannel>) channel).setSocket(sock);
        } else {
            assert false : "failed to create socket channel: " + sock + ", remote=" + remote + ", local=" + local;
        }
        // cache the channel
        Channel cached = setChannel(remote, local, channel);
        if (cached != null && cached != channel) {
            closeChannel(cached);
        }
    }

    @Override
    public Channel open(SocketAddress remote, SocketAddress local) {
        assert remote != null : "remote address empty";
        // get channel connected to remote address
        return getChannel(remote, local);
    }

}
