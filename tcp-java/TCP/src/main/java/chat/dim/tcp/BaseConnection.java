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

import chat.dim.mem.CachePool;
import chat.dim.mem.LockedPool;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class BaseConnection implements Connection, StateDelegate {

    private final StateMachine fsm;
    private final CachePool cachePool;

    private WeakReference<Delegate> delegateRef;

    protected Socket socket;

    long lastSentTime;
    long lastReceivedTime;

    public BaseConnection(Socket connectedSocket) {
        super();
        cachePool = createCachePool();
        delegateRef = null;
        socket = connectedSocket;
        lastSentTime = 0;
        lastReceivedTime = 0;
        // Finite State Machine
        fsm = new StateMachine();
        fsm.setDelegate(this);
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
    public Socket getSocket() {
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

    static boolean isAvailable(Socket sock) {
        if (sock == null || sock.isClosed()) {
            return false;
        } else {
            return sock.isConnected() || sock.isBound();
        }
    }

    @Override
    public boolean isRunning() {
        return isAvailable(socket);
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
            buffer = (new Data(buffer, 0, read)).getBytes();
        }
        lastReceivedTime = (new Date()).getTime();
        return buffer;
    }

    private void close() {
        Socket sock = socket;
        try {
            if (isAvailable(sock)) {
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
            changeState(ConnectionState.ERROR);
            return null;
        }
    }

    protected int send(byte[] data) {
        try {
            return write(data);
        } catch (IOException e) {
            // [TCP] failed to send data
            e.printStackTrace();
            close();
            changeState(ConnectionState.ERROR);
            return -1;
        }
    }

    @Override
    public int send(ByteArray data) {
        return send(data.getBytes());
    }

    @Override
    public int available() {
        return cachePool.length();
    }

    @Override
    public ByteArray receive(int maxLength) {
        return cachePool.shift(maxLength);
    }

    //
    //  Status
    //

    @Override
    public ConnectionState getState() {
        fsm.tick();
        return fsm.getCurrentState();
    }

    protected void changeState(String name) {
        ConnectionState oldState = fsm.getCurrentState();
        ConnectionState newState = fsm.getState(name);
        if (oldState == null) {
            if (newState != null) {
                fsm.changeState(newState);
            }
        } else if (newState == null) {
            fsm.changeState(null);
        } else if (!newState.equals(oldState)) {
            fsm.changeState(newState);
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
        changeState(ConnectionState.CONNECTING);
    }

    /**
     *  Cleanup after handling
     */
    public void finish() {
        close();  // shutdown socket
        changeState(ConnectionState.DEFAULT);
    }

    /**
     *  Handling for receiving data packages
     *  (it will call 'process()' circularly)
     */
    public void handle() {
        while (isRunning()) {
            if (!process()) {
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
        // check connection status
        ConnectionState state = fsm.getCurrentState();
        if (state == null) {
            return false;
        } else if (!state.name.equals(ConnectionState.CONNECTED) &&
                !state.name.equals(ConnectionState.MAINTAINING) &&
                !state.name.equals(ConnectionState.EXPIRED)) {
            // not connected yet
            return false;
        }
        // 1. try to read bytes
        byte[] buffer = receive();
        if (buffer == null || buffer.length == 0) {
            return false;
        }
        ByteArray data = new Data(buffer);
        // 2. cache it
        cachePool.push(data);
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
    //  Events
    //

    @Override
    public void enterState(ConnectionState state, StateMachine ctx) {
        ConnectionState old = ctx.getCurrentState();
        if (state != null && state.equals(ConnectionState.CONNECTED)) {
            if (old == null || !old.equals(ConnectionState.MAINTAINING)) {
                // change status to 'connected', reset times to just expired
                long now = (new Date()).getTime();
                lastSentTime = now - EXPIRES - 1;
                lastReceivedTime = now - EXPIRES - 1;
            }
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionStateChanged(this, old, state);
        }
    }

    @Override
    public void exitState(ConnectionState state, StateMachine ctx) {

    }

    @Override
    public void pauseState(ConnectionState state, StateMachine ctx) {

    }

    @Override
    public void resumeState(ConnectionState state, StateMachine ctx) {

    }
}
