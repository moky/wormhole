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
import java.net.InetAddress;
import java.net.Socket;
import java.net.SocketException;
import java.util.Date;

import chat.dim.mem.BytesArray;
import chat.dim.mem.CachePool;
import chat.dim.mem.LockedPool;

public class BaseConnection implements Connection {

    private final CachePool cachePool;

    private WeakReference<Delegate> delegateRef;

    protected Socket socket;
    private Status status;

    private long lastSentTime;
    private long lastReceivedTime;

    public BaseConnection(Socket connectedSocket) {
        super();
        cachePool = createCachePool();
        delegateRef = null;
        socket = connectedSocket;
        status = Status.DEFAULT;
        lastSentTime = 0;
        lastReceivedTime = 0;
    }

    // override for customized cache pool
    protected CachePool createCachePool() {
        return new LockedPool();
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

    /**
     *  Get connected socket
     */
    protected Socket getSocket() {
        if (isRunning()) {
            return socket;
        } else {
            return null;
        }
    }

    @Override
    public String getHost() {
        Socket sock = socket;
        if (sock == null) {
            return null;
        }
        InetAddress address = sock.getInetAddress();
        if (address == null) {
            return null;
        } else {
            return address.getHostAddress();
        }
    }

    @Override
    public int getPort() {
        Socket sock = socket;
        if (sock == null) {
            return 0;
        } else {
            return sock.getPort();
        }
    }

    @Override
    public boolean isRunning() {
        Socket sock = socket;
        if (sock == null || sock.isClosed()) {
            return false;
        } else {
            return sock.isConnected() || sock.isBound();
        }
    }

    private int write(byte[] data) throws IOException {
        Socket sock = getSocket();
        if (sock == null) {
            throw new SocketException("socket lost, cannot write data: " + data.length + " byte(s)");
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
            throw new SocketException("socket lost, cannot read data");
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
            buffer = BytesArray.slice(buffer, 0, read);
        }
        lastReceivedTime = (new Date()).getTime();
        return buffer;
    }

    private void close() {
        Socket sock = socket;
        try {
            if (sock != null && !sock.isClosed()) {
                sock.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            socket = null;
        }
    }

    protected byte[] receive() {
        try {
            return read();
        } catch (IOException e) {
            // [TCP] failed to receive data
            e.printStackTrace();
            close();
            setStatus(Status.ERROR);
            return null;
        }
    }

    @Override
    public int send(byte[] data) {
        try {
            return write(data);
        } catch (IOException e) {
            // [TCP] failed to send data
            e.printStackTrace();
            close();
            setStatus(Status.ERROR);
            return -1;
        }
    }

    @Override
    public int available() {
        return cachePool.length();
    }

    @Override
    public byte[] received() {
        return cachePool.all();
    }

    @Override
    public byte[] receive(int maxLength) {
        return cachePool.shift(maxLength);
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
        Status oldStatus = status;
        if (oldStatus.equals(newStatus)) {
            return;
        }
        status = newStatus;
        if (newStatus.equals(Status.CONNECTED) && !oldStatus.equals(Status.MAINTAINING)) {
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

    @Override
    public void stop() {
        close();  // shutdown socket
    }

    /**
     *  Prepare before handling
     */
    public void setup() {
        setStatus(Status.CONNECTING);
    }

    /**
     *  Cleanup after handling
     */
    public void finish() {
        close();  // shutdown socket
        setStatus(Status.DEFAULT);
    }

    /**
     *  Handling for receiving data packages
     *  (it will call 'process()' circularly)
     */
    public void handle() {
        boolean working;
        while (isRunning()) {
            switch (getStatus()) {
                case CONNECTED:
                case MAINTAINING:
                case EXPIRED:
                    working = process();
                    break;
                default:
                    working = false;
                    break;
            }
            if (!working) {
                idle();
            }
        }
    }

    /**
     *  Try to receive one data package,
     *  which will be cached into a memory pool
     */
    public boolean process() {
        // 0. check empty spaces
        int count = cachePool.length();
        if (count >= MAX_CACHE_LENGTH) {
            // not enough spaces
            return false;
        }
        // 1. try to read bytes
        byte[] data = receive();
        if (data == null || data.length == 0) {
            return false;
        }
        // 2. cache it
        cachePool.push(data);
        Delegate delegate = getDelegate();
        if (delegate != null) {
            // 3. callback
            delegate.onConnectionReceivedData(this, data);
        }
        return true;
    }

    protected void idle() {
        try {
            Thread.sleep(128);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    //
    //  Finite State Machine
    //

    private void fsmTick(long now) {
        switch (status) {
            case CONNECTED: {
                tickConnected(now);
                break;
            }
            case MAINTAINING:
                tickMaintaining(now);
                break;
            case EXPIRED:
                tickExpired(now);
                break;
            case CONNECTING:
                tickConnecting();
                break;
            case ERROR:
                tickError();
                break;
            case DEFAULT:
                tickDefault();
                break;
            default:
                throw new IllegalStateException("Connection state error: " + status);
        }
    }

    // Connection not started yet
    private void tickDefault() {
        if (isRunning()) {
            // connection started, change status to 'connecting'
            setStatus(Status.CONNECTING);
        }
    }

    // Connection started, not connected yet
    private void tickConnecting() {
        if (!isRunning()) {
            // connection stopped, change status to 'not_connect'
            setStatus(Status.DEFAULT);
        } else if (getSocket() != null) {
            // connection connected, change status to 'connected'
            setStatus(Status.CONNECTED);
        }
    }

    // Normal status of connection
    private void tickConnected(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(Status.ERROR);
        } else if (now > lastReceivedTime + EXPIRES) {
            // long time no response, change status to 'maintain_expired'
            setStatus(Status.EXPIRED);
        }
    }

    // Long time no response, need maintaining
    private void tickExpired(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(Status.ERROR);
        } else if (now < lastSentTime + EXPIRES) {
            // sent recently, change status to 'maintaining'
            setStatus(Status.MAINTAINING);
        }
    }

    // Heartbeat sent, waiting response
    private void tickMaintaining(long now) {
        if (getSocket() == null) {
            // connection lost, change status to 'error'
            setStatus(Status.ERROR);
        } else if (now > lastReceivedTime + (EXPIRES << 4)) {
            // long long time no response, change status to 'error
            setStatus(Status.ERROR);
        } else if (now < lastReceivedTime + EXPIRES) {
            // received recently, change status to 'connected'
            setStatus(Status.CONNECTED);
        } else if (now > lastSentTime + EXPIRES) {
            // long time no sending, change status to 'maintain_expired'
            setStatus(Status.EXPIRED);
        }
    }

    // Connection lost
    private void tickError() {
        if (!isRunning()) {
            // connection stopped, change status to 'not_connect'
            setStatus(Status.DEFAULT);
        } else if (getSocket() != null) {
            // connection reconnected, change status to 'connected'
            setStatus(Status.CONNECTED);
        }
    }
}
