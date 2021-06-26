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
package chat.dim.net;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.util.Date;

import chat.dim.threading.Ticker;

public class BaseConnection implements Connection, StateDelegate, Ticker {

    /*  Maximum Transmission Unit
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     *
     *  Buffer size for receiving package
     */
    public static int MTU = 1472; // 1500 - 20 - 8

    public static long EXPIRES = 16 * 1000;  // 16 seconds

    private final StateMachine fsm;

    private WeakReference<Delegate> delegateRef;

    protected Channel channel;

    private long lastSentTime;
    private long lastReceivedTime;

    public BaseConnection(Channel byteChannel) {
        super();
        delegateRef = null;
        channel = byteChannel;
        lastSentTime = 0;
        lastReceivedTime = 0;
        // Finite State Machine
        fsm = new StateMachine(this);
        fsm.setDelegate(this);
        fsm.start();
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
     *  Get connected channel
     */
    public Channel getChannel() {
        Channel sock = channel;
        return isAlive(sock) ? sock : null;
    }

    @Override
    public SocketAddress getRemoteAddress() {
        Channel sock = channel;
        try {
            return sock == null ? null : sock.getRemoteAddress();
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    boolean isSentRecently(long now) {
        return now < lastSentTime + EXPIRES;
    }
    boolean isReceivedRecently(long now) {
        return now < lastReceivedTime + EXPIRES;
    }
    boolean isNotReceivedLongTimeAgo(long now) {
        return now > lastReceivedTime + (EXPIRES << 4);
    }

    private static boolean isAlive(Channel sock) {
        if (sock == null || sock.isClosed()) {
            return false;
        } else {
            return sock.isConnected() || sock.isBound();
        }
    }

    @Override
    public boolean isAlive() {
        return isAlive(channel);
    }

    @Override
    public boolean isOpen() {
        Channel sock = channel;
        return sock != null && sock.isOpen();
    }

    @Override
    public boolean isBound() {
        Channel sock = channel;
        return sock != null && sock.isBound();
    }

    @Override
    public boolean isConnected() {
        Channel sock = channel;
        return sock != null && sock.isConnected();
    }

    @Override
    public boolean isClosed() {
        Channel sock = channel;
        return sock != null && sock.isClosed();
    }

    private int write(byte[] data) throws IOException {
        Channel sock = getChannel();
        if (sock == null) {
            throw new SocketException("socket lost, cannot write data: " + data.length + " byte(s)");
        }
        ByteBuffer buffer = ByteBuffer.allocate(data.length);
        buffer.put(data);
        buffer.flip();
        int sent = sock.write(buffer);
        lastSentTime = (new Date()).getTime();
        return sent;
    }

    private byte[] read() throws IOException {
        Channel sock = getChannel();
        if (sock == null) {
            throw new SocketException("socket lost, cannot read data");
        }
        ByteBuffer buffer = ByteBuffer.allocate(MTU);
        int res = sock.read(buffer);
        if (res <= 0) {
            return null;
        }
        assert res == buffer.position() : "buffer error: " + res + ", " + buffer.position();
        byte[] data = new byte[res];
        buffer.flip();
        buffer.get(data);
        lastReceivedTime = (new Date()).getTime();
        return data;
    }

    @Override
    public void close() {
        Channel sock = channel;
        try {
            if (isAlive(sock)) {
                sock.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            channel = null;
            changeState(ConnectionState.DEFAULT);
        }
    }

    @Override
    public byte[] receive() {
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

    @Override
    public int send(byte[] data) {
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

    public void start() {
        fsm.start();
    }

    public void stop() {
        close();
        fsm.stop();
    }

    /**
     *  Try to receive one data package,
     *  which will be cached into a memory pool
     */
    @Override
    public void tick() {
        fsm.tick();
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
