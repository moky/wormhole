/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
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
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.ref.WeakReference;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketException;
import java.util.Date;

public class Connection extends Thread {

    // remote address
    public final String host;
    public final int port;

    // inner socket
    private Socket socket;

    private boolean running;

    // connection status
    private ConnectionStatus status;
    private long lastSentTime;
    private long lastReceivedTime;

    private WeakReference<ConnectionDelegate> delegateRef;

    public static long EXPIRES = 16 * 1000;  // milliseconds

    private final CachePool cachePool;

    public Connection(Socket connectedSocket,
                      String remoteHost, int remotePort) {
        super();
        socket = connectedSocket;
        host = remoteHost;
        port = remotePort;
        status = ConnectionStatus.Default;
        delegateRef = null;
        running = false;
        lastSentTime = 0;
        lastReceivedTime = 0;
        // cache pool
        cachePool = createCachePool();
    }

    public Connection(Socket clientSocket) {
        this(clientSocket, null, 0);
    }

    public Connection(String serverHost, int serverPort) {
        this(null, serverHost, serverPort);
    }
    public Connection(InetSocketAddress serverAddress) {
        this(null, serverAddress.getHostString(), serverAddress.getPort());
    }

    protected CachePool createCachePool() {
        return new MemoryCache();
    }

    /**
     *  Get socket
     *
     * @return opened socket
     */
    public Socket getSocket() {
        if (socket == null) {
            if (host == null || port == 0) {
                return null;
            }
            setStatus(ConnectionStatus.Connecting);
            try {
                socket = new Socket(host, port);
                setStatus(ConnectionStatus.Connected);
            } catch (IOException e) {
                e.printStackTrace();
                setStatus(ConnectionStatus.Error);
                return null;
            }
        }
        if (socket.isClosed()) {
            return null;
        }
        return socket;
    }

    private int write(byte[] data) throws IOException {
        Socket sock = getSocket();
        if (sock == null) {
            return -1;
        }
        OutputStream outputStream = sock.getOutputStream();
        outputStream.write(data);
        outputStream.flush();
        lastSentTime = (new Date()).getTime();
        return data.length;
    }

    private byte[] read() throws IOException {
        Socket sock = getSocket();
        if (sock == null) {
            return null;
        }
        InputStream inputStream = sock.getInputStream();
        int available = inputStream.available();
        if (available <= 0) {
            return null;
        }
        byte[] buffer = new byte[available];
        int read = inputStream.read(buffer);
        if (read <= 0) {
            throw new SocketException("failed to read buffer: " + read + ", available=" + available);
        }
        if (read < available) {
            // read partially
            byte[] part = new byte[read];
            System.arraycopy(buffer, 0, part, 0, read);
            buffer = part;
        }
        lastReceivedTime = (new Date()).getTime();
        return buffer;
    }

    //
    //  Connection status
    //

    void setStatus(ConnectionStatus newStatus) {
        if (newStatus.equals(status)) {
            return;
        }
        ConnectionStatus oldStatus = status;
        status = newStatus;
        if (newStatus.equals(ConnectionStatus.Connected) && !oldStatus.equals(ConnectionStatus.Maintaining)) {
            // change status to 'connected', reset times to expired
            long now = (new Date()).getTime();
            lastSentTime = now - EXPIRES - 1;
            lastReceivedTime = now - EXPIRES - 1;
        }
        // callback
        ConnectionDelegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionStatusChanged(this, oldStatus, newStatus);
        }
    }

    public ConnectionStatus getStatus() {
        return status;
    }
    public ConnectionStatus getStatus(long now) {
        fsmTick(now);
        return status;
    }
    public ConnectionStatus getStatus(Date now) {
        return getStatus(now.getTime());
    }

    //
    //  Connection Delegate
    //

    public void setDelegate(ConnectionDelegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }

    public ConnectionDelegate getDelegate() {
        if (delegateRef == null) {
            return null;
        } else {
            return delegateRef.get();
        }
    }

    /**
     *  Get received data from cache, but not remove
     *
     * @return received data
     */
    public byte[] received() {
        return cachePool.received();
    }

    /**
     *  Get received data from cache, and remove it
     *  (call received() to check data first)
     *
     * @param length - how many bytes to receive
     * @return received data
     */
    public byte[] receive(int length) {
        return cachePool.receive(length);
    }

    /**
     *  Send data package
     *
     * @param data - package
     * @return -1 on error
     */
    public int send(byte[] data) {
        try {
            return write(data);
        } catch (IOException e) {
            e.printStackTrace();
            socket = null;
            setStatus(ConnectionStatus.Error);
            return -1;
        }
    }

    private byte[] receive() {
        try {
            return read();
        } catch (IOException e) {
            e.printStackTrace();
            socket = null;
            setStatus(ConnectionStatus.Error);
            return null;
        }
    }

    public void handle() {
        // 1. try to read bytes
        byte[] data = receive();
        if (data != null) {
            // 2. cache it
            byte[] ejected = cachePool.cache(data);
            // 3. callback
            ConnectionDelegate delegate = getDelegate();
            if (delegate != null) {
                if (ejected != null) {
                    delegate.onConnectionOverflowed(this, ejected);
                }
                delegate.onConnectionReceivedData(this, data);
            }
        }
    }

    @Override
    public void run() {
        running = true;
        while (running) {
            try {
                fsmTick(new Date());
                handle();
            } catch (Exception error) {
                error.printStackTrace();
            }
        }
    }

    public void close() {
        running = false;
        // shutdown socket
        if (socket != null) {
            try {
                socket.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
            socket = null;
        }
        setStatus(ConnectionStatus.Default);
    }

    //
    //  Finite State Machine
    //

    private void fsmTick(Date now) {
        fsmTick(now.getTime());
    }
    private void fsmTick(long now) {
        switch (status) {
            case Connected: {
                tickConnected(now);
                break;
            }
            case Maintaining:
                tickMaintaining(now);
                break;
            case Expired:
                tickExpired(now);
                break;
            case Connecting:
                tickConnecting();
                break;
            case Error:
                tickError();
                break;
            case Default:
                tickDefault();
                break;
        }
    }

    // Connection not started yet
    private void tickDefault() {
        if (running) {
            // connection started, change status to 'connecting'
            setStatus(ConnectionStatus.Connecting);
        }
    }

    // Connection started, not connected yet
    private void tickConnecting() {
        if (!running) {
            // connection stopped, change status to 'not_connect'
            setStatus(ConnectionStatus.Default);
        } else if (getSocket() != null) {
            // connection connected, change status to 'connected'
            setStatus(ConnectionStatus.Connected);
        }
    }

    // Normal status of connection
    private void tickConnected(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(ConnectionStatus.Error);
        } else if (now > lastReceivedTime + EXPIRES) {
            // long time no response, change status to 'maintain_expired'
            setStatus(ConnectionStatus.Expired);
        }
    }

    // Long time no response, need maintaining
    private void tickExpired(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(ConnectionStatus.Error);
        } else if (now < lastSentTime + EXPIRES) {
            // sent recently, change status to 'maintaining'
            setStatus(ConnectionStatus.Maintaining);
        }
    }

    // Heartbeat sent, waiting response
    private void tickMaintaining(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(ConnectionStatus.Error);
        } else if (now > lastReceivedTime + (EXPIRES << 4)) {
            // long long time no response, change status to 'error
            setStatus(ConnectionStatus.Error);
        } else if (now < lastReceivedTime + EXPIRES) {
            // received recently, change status to 'connected'
            setStatus(ConnectionStatus.Connected);
        } else if (now > lastSentTime + EXPIRES) {
            // long time no sending, change status to 'maintain_expired'
            setStatus(ConnectionStatus.Expired);
        }
    }

    // Connection lost
    private void tickError() {
        if (!running) {
            // connection stopped, change status to 'not_connect'
            setStatus(ConnectionStatus.Default);
        } else if (getSocket() != null) {
            // connection reconnected, change status to 'connected'
            setStatus(ConnectionStatus.Connected);
        }
    }
}
