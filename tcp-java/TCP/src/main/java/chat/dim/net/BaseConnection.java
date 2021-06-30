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

    public static long EXPIRES = 16 * 1000;  // 16 seconds

    private final StateMachine fsm;

    private WeakReference<Delegate> delegateRef;

    protected Channel channel;

    protected long lastSentTime;
    protected long lastReceivedTime;

    public BaseConnection(Channel byteChannel) {
        super();
        delegateRef = null;
        channel = byteChannel;
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
    public boolean equals(Connection other) {
        if (other == null) {
            return false;
        } else if (other == this) {
            return true;
        }
        return addressEqual(getRemoteAddress(), other.getRemoteAddress()) &&
                addressEqual(getLocalAddress(), other.getLocalAddress());
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
            assert local != null : "both local & remote address are empty";
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
        try {
            return sock == null ? null : sock.getLocalAddress();
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
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
        Channel sock = channel;
        try {
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
        Channel sock = channel;
        if (sock == null || !sock.isOpen()) {
            throw new SocketException("connection lost: " + sock);
        }
        return sock;
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        try {
            SocketAddress remote = getChannel().receive(dst);
            if (remote != null) {
                lastReceivedTime = (new Date()).getTime();
            }
            return remote;
        } catch (IOException e) {
            // [TCP] failed to receive data
            e.printStackTrace();
            close();
            changeState(ConnectionState.ERROR);
            return null;
        }
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        try {
            int sent = getChannel().send(src, target);
            if (sent != -1) {
                lastSentTime = (new Date()).getTime();
            }
            return sent;
        } catch (IOException e) {
            // [TCP] failed to send data
            e.printStackTrace();
            close();
            changeState(ConnectionState.ERROR);
            return -1;
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
        fsm.tick();
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
        close();
        fsm.stop();
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
