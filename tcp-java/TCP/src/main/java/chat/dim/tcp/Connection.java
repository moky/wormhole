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
import java.net.Socket;
import java.net.SocketAddress;
import java.util.Date;

public class Connection extends Thread {

    // remote address
    public final SocketAddress address;
    public final String host;
    public final int port;

    // inner socket
    Socket socket;
    private boolean running = false;

    // connection status
    private ConnectionStatus status = ConnectionStatus.Default;
    private long lastSentTime;
    private long lastReceivedTime;

    private WeakReference<ConnectionHandler> delegateRef = null;

    public static long EXPIRES = 28 * 1000;  // milliseconds

    private final CachePool cachePool;

    Connection(Socket connectedSocket,
               SocketAddress remoteAddress,
               String remoteHost, int remotePort) {
        super();
        socket = connectedSocket;
        address = remoteAddress;
        host = remoteHost;
        port = remotePort;
        // initialize times to expired
        long now = (new Date()).getTime();
        lastSentTime = now - EXPIRES - 1;
        lastReceivedTime = now - EXPIRES - 1;
        // cache pool
        cachePool = new MemoryCache();
    }

    public void setDelegate(ConnectionHandler delegate) {
        delegateRef = new WeakReference<>(delegate);
    }

    private ConnectionHandler getDelegate() {
        if (delegateRef == null) {
            return null;
        }
        return delegateRef.get();
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
        // callback
        ConnectionHandler delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionStatusChanged(this, oldStatus, newStatus);
        }
    }

    public boolean isConnected(long now) {
        return getStatus(now).isConnected();
    }

    public boolean isExpired(long now) {
        return getStatus(now).isExpired();
    }

    public boolean isError(long now) {
        return getStatus(now).isError();
    }

    /**
     *  Get connection status
     *
     * @param now - timestamp in milliseconds
     * @return new status
     */
    public ConnectionStatus getStatus(long now) {
        // pre-checks
        if (now < lastReceivedTime + EXPIRES) {
            // received response recently
            if (now < lastSentTime + EXPIRES) {
                // sent recently, set status = 'connected'
                setStatus(ConnectionStatus.Connected);
            } else {
                // long time no sending, set status = 'maintain_expired'
                setStatus(ConnectionStatus.Expired);
            }
            return status;
        }
        if (!status.equals(ConnectionStatus.Default)) {
            // any status except 'initialized'
            if (now > lastReceivedTime + (EXPIRES << 2)) {
                // long long time no response, set status = 'error'
                setStatus(ConnectionStatus.Error);
                return status;
            }
        }
        // check with current status
        switch (status) {
            case Default: {
                if (now < lastSentTime + EXPIRES) {
                    // sent recently, change status to 'connecting'
                    setStatus(ConnectionStatus.Connecting);
                }
                break;
            }

            case Connecting: {
                if (now > lastSentTime + EXPIRES) {
                    // long time no sending, change status to 'not_connect'
                    setStatus(ConnectionStatus.Default);
                }
                break;
            }

            case Connected: {
                if (now > lastReceivedTime + EXPIRES) {
                    // long time no response, needs maintaining
                    if (now < lastSentTime + EXPIRES) {
                        // sent recently, change status to 'maintaining'
                        setStatus(ConnectionStatus.Maintaining);
                    } else {
                        // long time no sending, change status to 'maintain_expired'
                        setStatus(ConnectionStatus.Expired);
                    }
                }
                break;
            }

            case Expired: {
                if (now < lastSentTime + EXPIRES) {
                    // sent recently, change status to 'maintaining'
                    setStatus(ConnectionStatus.Maintaining);
                }
                break;
            }

            case Maintaining: {
                if (now > lastSentTime + EXPIRES) {
                    // long time no sending, change status to 'maintain_expired'
                    setStatus(ConnectionStatus.Expired);
                }
                break;
            }

            default: {
                break;
            }
        }
        return status;
    }

    /**
     *  Update last sent time
     *
     * @param now - milliseconds
     */
    private void updateSentTime(long now) {
        lastSentTime = now;
    }

    /**
     *  Update last received time
     *
     * @param now - milliseconds
     */
    private void updateReceivedTime(long now) {
        lastReceivedTime = now;
    }

    protected byte[] read() throws IOException {
        InputStream inputStream = socket.getInputStream();
        int length = inputStream.available();
        if (length <= 0) {
            return null;
        }
        byte[] buffer = new byte[length];
        int count = inputStream.read(buffer);
        long now = (new Date()).getTime();
        updateReceivedTime(now);
        if (count == length) {
            return buffer;
        }
        assert count < length : "read error: " + count + ", " + length;
        byte[] available = new byte[count];
        System.arraycopy(buffer, 0, available, 0, count);
        return available;
    }

    protected int write(byte[] data) throws IOException {
        OutputStream outputStream = socket.getOutputStream();
        outputStream.write(data);
        long now = (new Date()).getTime();
        updateSentTime(now);
        return data.length;
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
            return -1;
        }
    }

    /**
     *  Get received data from buffer, but not remove from the cache
     *
     * @return received data
     */
    public byte[] received() {
        return cachePool.received();
    }

    /**
     *  Get received data from buffer, and remove it from the cache
     *  (remember call received() to check data first)
     *
     * @param length - how many bytes to receive
     * @return received data
     */
    public byte[] receive(int length) {
        return cachePool.receive(length);
    }

    void _sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void start() {
        running = true;
        super.start();
    }

    public void close() {
        running = false;
    }

    @Override
    public void run() {
        byte[] data;
        ConnectionHandler delegate;
        while (running) {
            // 1. try to read bytes
            try {
                data = read();
            } catch (IOException e) {
                e.printStackTrace();
                break;
            }
            if (data == null) {
                // received nothing, have a rest, ^_^
                _sleep(100);
                continue;
            }
            data = cachePool.cache(data);
            delegate = getDelegate();
            if (delegate != null) {
                if (data == null) {
                    delegate.onConnectionReceivedData(this);
                } else {
                    delegate.onConnectionOverflowed(this, data);
                }
            }
        }
    }
}
