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

public class BaseConnection implements Connection, StateDelegate {

    /*  Maximum Segment Size
     *  ~~~~~~~~~~~~~~~~~~~~
     *  Buffer size for receiving package
     *
     *  MTU        : 1500 bytes (excludes 14 bytes ethernet header & 4 bytes FCS)
     *  IP header  :   20 bytes
     *  TCP header :   20 bytes
     *  UDP header :    8 bytes
     */
    public static int MSS = 1472;  // 1500 - 20 - 8

    public static long EXPIRES = 16 * 1000;  // 16 seconds

    private final StateMachine fsm;

    private WeakReference<Delegate> delegateRef;

    protected Channel channel;

    protected final SocketAddress localAddress;
    protected final SocketAddress remoteAddress;

    private long lastSentTime;
    private long lastReceivedTime;

    public BaseConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super();
        delegateRef = null;
        channel = byteChannel;
        remoteAddress = remote;
        localAddress = local;
        lastSentTime = 0;
        lastReceivedTime = 0;
        // Finite State Machine
        fsm = new StateMachine(this);
        fsm.setDelegate(this);
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

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        } else if (other instanceof Connection) {
            Connection conn = (Connection) other;
            return addressEqual(getRemoteAddress(), conn.getRemoteAddress()) &&
                    addressEqual(getLocalAddress(), conn.getLocalAddress());
        } else {
            return false;
        }
    }
    private static boolean addressEqual(SocketAddress address1, SocketAddress address2) {
        if (address1 == null) {
            return address2 == null;
        } else if (address2 == null) {
            return false;
        } else {
            return address1.equals(address2);
        }
    }

    @Override
    public int hashCode() {
        SocketAddress local = getLocalAddress();
        SocketAddress remote = getRemoteAddress();
        if (remote == null) {
            assert local != null : "both local & remote addresses are empty";
            return local.hashCode();
        } else {
            //  same algorithm as Pair::hashCode()
            //  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            //  remote's hashCode is multiplied by an arbitrary prime number (13)
            //  in order to make sure there is a difference in the hashCode between
            //  these two parameters:
            //      remote: a  local: aa
            //      local: aa  remote: a
            return remote.hashCode() * 13 + (local == null ? 0 : local.hashCode());
        }
    }

    @Override
    public SocketAddress getLocalAddress() {
        Channel sock = channel;
        if (sock != null && sock.isBound()) {
            try {
                return sock.getLocalAddress();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return localAddress;
    }

    @Override
    public SocketAddress getRemoteAddress() {
        Channel sock = channel;
        if (sock != null && sock.isConnected()) {
            try {
                return sock.getRemoteAddress();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return remoteAddress;
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
    public void close() {
        try {
            Channel sock = channel;
            if (sock != null && sock.isOpen()) {
                sock.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            channel = null;
            changeState(ConnectionState.DEFAULT);
        }
    }

    protected Channel getChannel() throws IOException {
        return channel;
    }

    protected SocketAddress receive(ByteBuffer dst) throws IOException {
        Channel sock = getChannel();
        if (sock == null || !sock.isOpen()) {
            throw new SocketException("connection lost: " + sock);
        }
        try {
            SocketAddress remote = sock.receive(dst);
            if (remote != null) {
                lastReceivedTime = (new Date()).getTime();
            }
            return remote;
        } catch (IOException e) {
            // [TCP] failed to receive data
            close();
            changeState(ConnectionState.ERROR);
            throw e;
        }
    }

    @Override
    public int send(byte[] data, SocketAddress destination) throws IOException {
        Channel sock = getChannel();
        if (sock == null || !sock.isOpen()) {
            throw new SocketException("connection lost: " + sock);
        }
        try {
            ByteBuffer buffer = ByteBuffer.allocate(data.length);
            buffer.put(data);
            buffer.flip();
            int sent = sock.send(buffer, destination);
            if (sent != -1) {
                lastSentTime = (new Date()).getTime();
            }
            return sent;
        } catch (IOException e) {
            // [TCP] failed to send data
            close();
            changeState(ConnectionState.ERROR);
            throw e;
        }
    }

    //
    //  States
    //

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

    @Override
    public ConnectionState getState() {
        return fsm.getCurrentState();
    }

    @Override
    public void tick() {
        fsm.tick();

        if (isOpen()) {
            // try to receive data when connection open
            try {
                process();
            } catch (IOException e) {
                //e.printStackTrace();
            }
        }
    }

    protected void process() throws IOException {
        Delegate delegate = getDelegate();
        if (delegate == null) {
            return;
        }
        // receiving
        ByteBuffer buffer = ByteBuffer.allocate(MSS);
        SocketAddress remote = receive(buffer);
        if (remote == null) {
            return;
        }
        byte[] data = new byte[buffer.position()];
        buffer.flip();
        buffer.get(data);
        // callback
        delegate.onConnectionReceivedData(this, remote, data);
    }

    public void start() {
        fsm.start();
    }

    public void stop() {
        close();
        fsm.stop();
    }

    //
    //  Events
    //

    @Override
    public void enterState(ConnectionState state, StateMachine ctx) {
        ConnectionState current = ctx.getCurrentState();
        if (state != null && state.equals(ConnectionState.CONNECTED)) {
            if (current == null || !current.equals(ConnectionState.MAINTAINING)) {
                // change state to 'connected', reset times to just expired
                long timestamp = (new Date()).getTime() - EXPIRES - 1;
                lastSentTime = timestamp;
                lastReceivedTime = timestamp;
            }
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionStateChanging(this, current, state);
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
