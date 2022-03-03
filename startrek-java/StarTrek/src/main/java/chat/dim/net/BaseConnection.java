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
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.util.Date;

import chat.dim.type.AddressPairObject;

interface TimedConnection {

    long getLastSentTime();

    long getLastReceivedTime();

    boolean isSentRecently(long now);

    boolean isReceivedRecently(long now);

    boolean isNotReceivedLongTimeAgo(long now);
}

public class BaseConnection extends AddressPairObject implements Connection, TimedConnection, StateDelegate {

    public static long EXPIRES = 16 * 1000;  // 16 seconds

    private Channel channel;

    private long lastSentTime;
    private long lastReceivedTime;

    private final WeakReference<Delegate> delegateRef;
    private final WeakReference<Hub> hubRef;

    private final StateMachine fsm;

    public BaseConnection(SocketAddress remote, SocketAddress local, Channel sock, Delegate delegate, Hub hub) {
        super(remote, local);

        channel = sock;

        lastSentTime = 0;
        lastReceivedTime = 0;

        delegateRef = new WeakReference<>(delegate);
        hubRef = new WeakReference<>(hub);

        // Finite State Machine
        fsm = createStateMachine();
    }

    protected StateMachine createStateMachine() {
        StateMachine machine = new StateMachine(this);
        machine.setDelegate(this);
        return machine;
    }

    protected Delegate getDelegate() {
        return delegateRef.get();
    }

    protected Hub getHub() {
        return hubRef.get();
    }

    protected Channel getChannel() {
        return channel;
    }
    protected void setChannel(Channel sock) {
        channel = sock;
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
        fsm.stop();
    }

    private void closeChannel() {
        Channel sock = channel;
        if (sock == null) {
            return;
        } else {
            channel = null;
        }
//        Hub hub = getHub();
//        if (hub != null) {
//            hub.closeChannel(sock);
//        }
    }

    @Override
    public long getLastSentTime() {
        return lastSentTime;
    }

    @Override
    public long getLastReceivedTime() {
        return lastReceivedTime;
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
        return now > lastReceivedTime + (EXPIRES << 3);
    }

    @Override
    public void received(byte[] data, SocketAddress remote, SocketAddress local) {
        lastReceivedTime = (new Date()).getTime();  // update received time
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onReceived(data, remote, local, this);
        }
    }

    protected int send(ByteBuffer src, SocketAddress destination) throws IOException {
        Channel sock = getChannel();
        if (sock == null || !sock.isAlive()) {
            throw new SocketException("socket channel lost");
        }
        int sent = sock.send(src, destination);
        if (sent != -1) {
            lastSentTime = (new Date()).getTime();  // update sent time
        }
        return sent;
    }

    @Override
    public int send(byte[] pack, SocketAddress destination) {
        // prepare buffer
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
                closeChannel();
            }
        } catch (IOException e) {
            //e.printStackTrace();
            error = e;
            closeChannel();
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            // get local address as source
            SocketAddress source = localAddress;
            if (source == null) {
                Channel sock = channel;
                if (sock != null) {
                    source = sock.getLocalAddress();
                }
            }
            if (error == null) {
                delegate.onSent(pack, source, destination, this);
            } else {
                delegate.onError(error, pack, source, destination, this);
            }
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
        // drive state machine forward
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
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onStateChanged(previous, current, this);
        }
    }

    @Override
    public void pauseState(ConnectionState current, StateMachine ctx) {

    }

    @Override
    public void resumeState(ConnectionState current, StateMachine ctx) {

    }
}
