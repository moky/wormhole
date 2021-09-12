/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
import java.nio.ByteBuffer;
import java.util.Date;

interface TimedConnection {

    boolean isSentRecently(long now);

    boolean isReceivedRecently(long now);

    boolean isNotReceivedLongTimeAgo(long now);
}

public class BaseConnection implements Connection, TimedConnection, StateDelegate {

    public static long EXPIRES = 16 * 1000;  // 16 seconds

    private Channel channel;
    protected final SocketAddress localAddress;
    protected final SocketAddress remoteAddress;

    private long lastSentTime;
    private long lastReceivedTime;

    private WeakReference<Delegate> delegateRef;
    private WeakReference<Hub> hubRef;

    private final StateMachine fsm;

    public BaseConnection(Channel sock, SocketAddress remote, SocketAddress local) {
        super();
        channel = sock;
        remoteAddress = remote;
        localAddress = local;

        lastSentTime = 0;
        lastReceivedTime = 0;

        delegateRef = null;
        hubRef = null;
        // Finite State Machine
        fsm = getStateMachine();
    }

    protected StateMachine getStateMachine() {
        StateMachine machine = new StateMachine(this);
        machine.setDelegate(this);
        return machine;
    }

    public Delegate getDelegate() {
        return delegateRef.get();
    }
    public void setDelegate(Delegate delegate) {
        delegateRef = new WeakReference<>(delegate);
    }

    public Hub getHub() {
        return hubRef.get();
    }
    public void setHub(Hub hub) {
        hubRef = new WeakReference<>(hub);
    }

    protected Channel getChannel() {
        return channel;
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
        return localAddress;
    }

    @Override
    public SocketAddress getRemoteAddress() {
        return remoteAddress;
    }

    @Override
    public boolean isOpen() {
        Channel sock = getChannel();
        return sock != null && sock.isOpen();
    }

    @Override
    public boolean isBound() {
        Channel sock = getChannel();
        return sock != null && sock.isBound();
    }

    @Override
    public boolean isConnected() {
        Channel sock = getChannel();
        return sock != null && sock.isConnected();
    }

    @Override
    public boolean isAlive() {
        return isOpen() && (isConnected() || isBound());
    }

    @Override
    public void close() {
        closeChannel();
    }

    private void closeChannel() {
        if (channel == null) {
            return;
        }
        getHub().closeChannel(channel);
        channel = null;
    }

    @Override
    public boolean isSentRecently(long now) {
        return now < lastSentTime + EXPIRES;
    }
    @Override
    public boolean isReceivedRecently(long now) {
        return now < lastReceivedTime + EXPIRES;
    }
    @Override
    public boolean isNotReceivedLongTimeAgo(long now) {
        return now > lastReceivedTime + (EXPIRES << 4);
    }

    @Override
    public void received(byte[] data) {
        lastReceivedTime = (new Date()).getTime();  // update received time
        getDelegate().onReceived(data, remoteAddress, localAddress, this);
    }

    protected int send(ByteBuffer src, SocketAddress destination) throws IOException {
        Channel channel = getChannel();
        int sent = channel.send(src, destination);
        if (sent != -1) {
            lastSentTime = (new Date()).getTime();  // update sent time
        }
        return sent;
    }

    @Override
    public int send(byte[] pack, SocketAddress destination) {
        ByteBuffer buffer = ByteBuffer.allocate(pack.length);
        buffer.put(pack);
        buffer.flip();
        // try to send data
        Throwable error = null;
        int sent = -1;
        try {
            sent = send(buffer, destination);
            if (sent == -1) {
                error = new Error("failed to send data: " + pack.length + " byte(s) to " + destination);
            }
        } catch (IOException e) {
            e.printStackTrace();
            error = e;
        }
        if (error == null) {
            getDelegate().onSent(pack, getLocalAddress(), destination, this);
        } else {
            getDelegate().onError(error, pack, getLocalAddress(), destination, this);
        }
        return sent;
    }

    //
    //  States
    //

    @Override
    public ConnectionState getState() {
        return fsm.getCurrentState();
    }

    @Override
    public void tick() {
        fsm.tick();
    }

    public void start() {
        fsm.start();
    }

    public void stop() {
        closeChannel();
        fsm.stop();
    }

    //
    //  Events
    //

    @Override
    public void enterState(ConnectionState next, StateMachine ctx) {

    }

    @Override
    public void exitState(ConnectionState previous, StateMachine ctx) {
        ConnectionState current = ctx.getCurrentState();
        if (current != null && current.equals(ConnectionState.READY)) {
            if (previous == null || !previous.equals(ConnectionState.MAINTAINING)) {
                // change state to 'ready', reset times to just expired
                long timestamp = (new Date()).getTime() - EXPIRES - 1;
                lastSentTime = timestamp;
                lastReceivedTime = timestamp;
            }
        }
        // callback
        getDelegate().onStateChanged(previous, current, this);
    }

    @Override
    public void pauseState(ConnectionState current, StateMachine ctx) {

    }

    @Override
    public void resumeState(ConnectionState current, StateMachine ctx) {

    }
}
