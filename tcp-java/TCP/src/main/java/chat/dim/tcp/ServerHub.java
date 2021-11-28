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

public class ServerHub extends StreamHub implements Runnable {

    private SocketAddress localAddress = null;
    private ServerSocketChannel master = null;
    // running thread
    private Thread thread = null;
    private boolean running = false;

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Connection createConnection(Channel sock, SocketAddress remote, SocketAddress local) {
        BaseConnection conn = new BaseConnection(remote, null, sock, getDelegate(), this);
        conn.start();  // start FSM
        return conn;
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
        forceStop();
        running = true;
        thread = new Thread(this);
        thread.start();
    }

    private void forceStop() {
        running = false;
        if (thread != null && thread.isAlive()) {
            thread.interrupt();
        }
        thread = null;
    }

    public void stop() {
        forceStop();
    }

    public boolean isRunning() {
        return running;
    }

    @Override
    public void run() {
        SocketChannel sock;
        SocketAddress remote;
        running = true;
        while (isRunning()) {
            try {
                sock = master.accept();
                if (sock != null) {
                    remote = sock.getRemoteAddress();
                    putChannel(new StreamChannel(sock, remote, localAddress));
                }
            } catch (IOException e) {
                //e.printStackTrace();
            }
        }
    }
}
