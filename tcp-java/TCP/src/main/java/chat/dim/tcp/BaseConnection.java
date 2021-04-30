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
import java.net.SocketException;
import java.util.Date;

public class BaseConnection implements Connection, Runnable {

    private final CachePool cachePool;

    private WeakReference<Delegate> delegateRef;

    protected Socket socket;
    private Status status;

    protected boolean running;
    private long lastSentTime;
    private long lastReceivedTime;

    public static long EXPIRES = 16 * 1000;  // 16 seconds

    public BaseConnection(Socket connectedSocket) {
        super();
        cachePool = createCachePool();
        delegateRef = null;
        socket = connectedSocket;
        status = Status.Default;
        running = false;
        lastSentTime = 0;
        lastReceivedTime = 0;
    }

    // override for customized cache pool
    protected CachePool createCachePool() {
        return new MemoryCache();
    }

    public Delegate getDelegate() {
        if (delegateRef == null) {
            return null;
        } else {
            return delegateRef.get();
        }
    }
    public void setDelegate(Delegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }

    //
    //  Socket
    //

    protected Socket getSocket() {
        if (socket != null && socket.isConnected()) {
            return socket;
        } else {
            return null;
        }
    }

    private int write(byte[] data) throws IOException {
        assert !socket.isClosed() : "cannot write data when socket is closed: " + socket;
        OutputStream outputStream = socket.getOutputStream();
        outputStream.write(data);
        outputStream.flush();
        lastSentTime = (new Date()).getTime();
        return data.length;
    }

    private byte[] read() throws IOException {
        assert !socket.isClosed() : "cannot read data when socket is closed: " + socket;
        InputStream inputStream = socket.getInputStream();
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

    private void close() {
        assert socket != null : "socket not found";
        try {
            socket.close();
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            socket = null;
        }
    }

    protected byte[] receive() {
        Socket sock = getSocket();
        if (sock != null) {
            try {
                return read();
            } catch (IOException e) {
                e.printStackTrace();
                close();
            }
        }
        setStatus(Status.Error);
        return null;
    }

    @Override
    public int send(byte[] data) {
        Socket sock = getSocket();
        if (sock != null) {
            try {
                return write(data);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        socket = null;
        setStatus(Status.Error);
        return -1;
    }

    @Override
    public byte[] received() {
        return cachePool.received();
    }

    @Override
    public byte[] receive(int length) {
        return cachePool.receive(length);
    }

    //
    //  Status
    //

    @Override
    public Status getStatus() {
        Date now = new Date();
        fsmTick(now.getTime());
        return status;
    }

    protected void setStatus(Status newStatus) {
        if (newStatus.equals(status)) {
            return;
        }
        Status oldStatus = status;
        status = newStatus;
        if (newStatus.equals(Status.Connected) && !oldStatus.equals(Status.Maintaining)) {
            // change status to 'connected', reset times to just expired
            long now = (new Date()).getTime();
            lastSentTime = now - EXPIRES - 1;
            lastReceivedTime = now - EXPIRES - 1;
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionStatusChanged(this, oldStatus, newStatus);
        }
    }

    public boolean isRunning() {
        return running && socket != null;
    }

    //
    //  Running
    //

    @Override
    public void run() {
        setup();
        try {
            handle();
        } finally {
            finish();
        }
    }

    public void stop() {
        running = false;
    }

    /**
     *  Prepare before handling
     */
    public void setup() {
        running = true;
        setStatus(Status.Connecting);
    }

    /**
     *  Cleanup after handling
     */
    public void finish() {
        // shutdown socket
        if (socket != null) {
            close();
        }
        setStatus(Status.Default);
    }

    /**
     *  Handling for receiving data packages
     *  (it will call 'process()' circularly)
     */
    public void handle() {
        while (isRunning()) {
            Status s = getStatus();
            if (s.equals(Status.Connected) || s.equals(Status.Maintaining) || s.equals(Status.Expired)) {
                process();
            }
        }
    }

    /**
     *  Try to receive one data package,
     *  which will be cached into a memory pool
     */
    public void process() {
        // 1. try to read bytes
        byte[] data = receive();
        if (data == null) {
            return;
        }
        // 2. cache it
        byte[] ejected = cachePool.cache(data);
        Delegate delegate = getDelegate();
        if (delegate == null) {
            return;
        }
        // 3. callback
        if (ejected != null) {
            delegate.onConnectionOverflowed(this, ejected);
        }
        delegate.onConnectionReceivedData(this, data);
    }

    //
    //  Finite State Machine
    //

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
            setStatus(Status.Connecting);
        }
    }

    // Connection started, not connected yet
    private void tickConnecting() {
        if (!running) {
            // connection stopped, change status to 'not_connect'
            setStatus(Status.Default);
        } else if (getSocket() != null) {
            // connection connected, change status to 'connected'
            setStatus(Status.Connected);
        }
    }

    // Normal status of connection
    private void tickConnected(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(Status.Error);
        } else if (now > lastReceivedTime + EXPIRES) {
            // long time no response, change status to 'maintain_expired'
            setStatus(Status.Expired);
        }
    }

    // Long time no response, need maintaining
    private void tickExpired(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(Status.Error);
        } else if (now < lastSentTime + EXPIRES) {
            // sent recently, change status to 'maintaining'
            setStatus(Status.Maintaining);
        }
    }

    // Heartbeat sent, waiting response
    private void tickMaintaining(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(Status.Error);
        } else if (now > lastReceivedTime + (EXPIRES << 4)) {
            // long long time no response, change status to 'error
            setStatus(Status.Error);
        } else if (now < lastReceivedTime + EXPIRES) {
            // received recently, change status to 'connected'
            setStatus(Status.Connected);
        } else if (now > lastSentTime + EXPIRES) {
            // long time no sending, change status to 'maintain_expired'
            setStatus(Status.Expired);
        }
    }

    // Connection lost
    private void tickError() {
        if (!running) {
            // connection stopped, change status to 'not_connect'
            setStatus(Status.Default);
        } else if (getSocket() != null) {
            // connection reconnected, change status to 'connected'
            setStatus(Status.Connected);
        }
    }
}
