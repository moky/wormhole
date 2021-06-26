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
import java.net.Socket;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class ActiveConnection extends BaseConnection {

    // remote address
    public final String host;
    public final int port;

    private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();
    private int connecting;

    private boolean running;

    public ActiveConnection(String remoteHost, int remotePort, Socket connectedSocket) {
        super(connectedSocket);
        assert remoteHost != null && remotePort > 0 : "remote address error (" + remoteHost + ":" + remotePort + ")";
        host = remoteHost;
        port = remotePort;
        connecting = 0;
        running = false;
    }

    /**
     public ActiveConnection(Socket connectedSocket) {
     this(connectedSocket.getInetAddress().getHostAddress(), connectedSocket.getPort(), connectedSocket);
     }
     */

    public ActiveConnection(String serverHost, int serverPort) {
        this(serverHost, serverPort, null);
    }

    private boolean connect() {
        changeState(ConnectionState.CONNECTING);
        try {
            socket = new Socket(host, port);
            changeState(ConnectionState.CONNECTED);
            return true;
        } catch (IOException e) {
            e.printStackTrace();
            changeState(ConnectionState.ERROR);
            return false;
        }
    }
    private boolean reconnect() {
        boolean redo;
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            connecting += 1;
            if (connecting == 1 && socket == null) {
                redo = connect();
            } else {
                redo = false;
            }
        } finally {
            connecting -= 1;
            writeLock.unlock();
        }
        return redo;
    }

    @Override
    public Socket getSocket() {
        if (isRunning()) {
            if (socket == null) {
                reconnect();
            }
            return socket;
        } else {
            return null;
        }
    }

    @Override
    public String getHost() {
        return host;
    }

    @Override
    public int getPort() {
        return port;
    }

    @Override
    public boolean isRunning() {
        return running;
    }

    @Override
    protected byte[] receive() {
        byte[] data = super.receive();
        if (data == null && reconnect()) {
            // try again
            data = super.receive();
        }
        return data;
    }

    @Override
    public int send(byte[] data) {
        int res = super.send(data);
        if (res < 0 && reconnect()) {
            // try again
            res = super.send(data);
        }
        return res;
    }

    @Override
    public void run() {
        running = true;
        super.run();
    }

    @Override
    public void stop() {
        super.stop();
        running = false;
    }
}
