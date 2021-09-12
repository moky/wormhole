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

import chat.dim.net.Connection;

public class ServerHub extends StreamHub implements Runnable {

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
        new Thread(this).start();
    }

    public void stop() {
        running = false;
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
                System.out.println("new channel: " + sock);
                if (sock != null) {
                    remote = sock.getRemoteAddress();
                    setChannel(remote, new StreamChannel(sock, remote, localAddress));
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
