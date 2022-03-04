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

    private WeakReference<Channel> channelRef;
    private final WeakReference<Delegate> delegateRef;

    private long lastSentTime;
    private long lastReceivedTime;

    private StateMachine fsm;

    public BaseConnection(SocketAddress remote, SocketAddress local, Channel sock, Delegate delegate) {
        super(remote, local);

        channelRef = new WeakReference<>(sock);
        delegateRef = new WeakReference<>(delegate);

        // active times
        lastSentTime = 0;
        lastReceivedTime = 0;

        // connection state machine
        fsm = null;
    }

    protected StateMachine getStateMachine() {
        return fsm;
    }
    protected void setStateMachine(StateMachine newMachine) {
        // 1. check old machine
        StateMachine oldMachine = fsm;
        if (oldMachine != null && oldMachine != newMachine) {
            oldMachine.stop();
        }
        // 2. set new machine
        fsm = newMachine;
    }
    protected StateMachine createStateMachine() {
        StateMachine machine = new StateMachine(this);
        machine.setDelegate(this);
        return machine;
    }

    protected Delegate getDelegate() {
        return delegateRef.get();
    }

    public Channel getChannel() {
        return channelRef == null ? null : channelRef.get();
    }
    protected void setChannel(Channel newChannel) {
        // 1. check old channel
        if (channelRef != null) {
            Channel oldChannel = channelRef.get();
            if (oldChannel != null && oldChannel != newChannel) {
                if (oldChannel.isOpen()) {
                    try {
                        oldChannel.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
        // 2. set new channel
        channelRef = newChannel == null ? null : new WeakReference<>(newChannel);
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
    public SocketAddress getLocalAddress() {
        Channel channel = getChannel();
        return channel == null ? localAddress : channel.getLocalAddress();
    }

    @Override
    public void close() {
        setChannel(null);
        setStateMachine(null);
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
            //throw new SocketException("socket channel lost");
            return -1;
        }
        int sent = sock.send(src, destination);
        if (sent > 0) {
            lastSentTime = (new Date()).getTime();  // update sent time
        }
        return sent;
    }

    @Override
    public int send(byte[] pack, SocketAddress destination) {
        // try to send data
        Throwable error = null;
        int sent = -1;
        try {
            // prepare buffer
            ByteBuffer buffer = ByteBuffer.allocate(pack.length);
            buffer.put(pack);
            buffer.flip();
            // send buffer
            sent = send(buffer, destination);
            if (sent < 0) {  // == -1
                error = new Error("failed to send data: " + pack.length + " byte(s) to " + destination);
            }
        } catch (IOException e) {
            //e.printStackTrace();
            error = e;
            // socket error, close current channel
            setChannel(null);
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            // get local address as source
            SocketAddress source = getLocalAddress();
            if (error == null) {
                if (sent <= 0) {
                    pack = new byte[0];
                } else if (sent < pack.length) {
                    byte[] data = new byte[sent];
                    System.arraycopy(pack, 0, data, 0, sent);
                    pack = data;
                }
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
        StateMachine machine = getStateMachine();
        return machine == null ? null : machine.getCurrentState();
    }

    @Override
    public void tick() {
        StateMachine machine = getStateMachine();
        if (machine != null) {
            machine.tick();
        }
    }

    public void start() {
        StateMachine machine = createStateMachine();
        machine.start();
        setStateMachine(machine);
    }

    public void stop() {
        setChannel(null);
        setStateMachine(null);
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
