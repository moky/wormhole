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
package chat.dim.socket;

import java.io.IOError;
import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.nio.ByteBuffer;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.StateMachine;
import chat.dim.net.TimedConnection;
import chat.dim.type.AddressPairObject;

public class BaseConnection extends AddressPairObject
        implements Connection, TimedConnection, ConnectionState.Delegate {

    public static long EXPIRES = 16 * 1000;  // 16 seconds

    private WeakReference<Channel> channelRef;
    private WeakReference<Delegate> delegateRef;

    private long lastSentTime;
    private long lastReceivedTime;

    private StateMachine fsm;

    public BaseConnection(SocketAddress remote, SocketAddress local, Channel sock) {
        super(remote, local);

        channelRef = new WeakReference<>(sock);
        delegateRef = new WeakReference<>(null);

        // active times
        lastSentTime = 0;
        lastReceivedTime = 0;

        // connection state machine
        fsm = null;
    }

    @Override
    protected void finalize() throws Throwable {
        // make sure the relative channel is closed
        setChannel(null);
        setStateMachine(null);
        super.finalize();
    }

    // connection state machine
    protected StateMachine getStateMachine() {
        return fsm;
    }
    private void setStateMachine(StateMachine newMachine) {
        // 1. replace with new machine
        StateMachine oldMachine = fsm;
        fsm = newMachine;
        // 2. stop old machine
        if (oldMachine != null && oldMachine != newMachine) {
            oldMachine.stop();
        }
    }
    protected StateMachine createStateMachine() {
        StateMachine machine = new StateMachine(this);
        machine.setDelegate(this);
        return machine;
    }

    // delegate for handling connection events
    public void setDelegate(Delegate delegate) {
        delegateRef = new WeakReference<>(delegate);
    }
    protected Delegate getDelegate() {
        return delegateRef.get();
    }

    // socket channel
    protected Channel getChannel() {
        return channelRef.get();
    }
    protected void setChannel(Channel newChannel) {
        // 1. replace with new channel
        Channel oldChannel = channelRef.get();
        channelRef = new WeakReference<>(newChannel);
        // 2. close old channel
        if (oldChannel != null && oldChannel != newChannel) {
            if (oldChannel.isConnected()) {
                try {
                    oldChannel.disconnect();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
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
        /// Channel sock = getChannel();
        /// return sock != null && sock.isAlive();
        return isOpen() && (isConnected() || isBound());
    }

    /*/
    @Override
    public SocketAddress getLocalAddress() {
        Channel channel = getChannel();
        return channel == null ? localAddress : channel.getLocalAddress();
    }
    /*/

    @Override
    public String toString() {
        String cname = getClass().getName();
        return "<" + cname + " remote=\"" + getRemoteAddress() + "\" local=\"" + getLocalAddress() + "\">\n\t"
                + channelRef.get() + "\n</" + cname + ">";
    }

    @Override
    public void close() {
        setChannel(null);
        setStateMachine(null);
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
    //  I/O
    //

    @Override
    public void onReceived(byte[] data) {
        lastReceivedTime = System.currentTimeMillis();  // update received time
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionReceived(data, this);
        }
    }

    protected int send(ByteBuffer src, SocketAddress destination) throws IOException {
        Channel sock = getChannel();
        if (sock == null || !sock.isAlive()) {
            //throw new IOException("socket channel lost: " + sock);
            return -1;
        }
        int sent = sock.send(src, destination);
        if (sent > 0) {
            // update sent time
            lastSentTime = System.currentTimeMillis();
        }
        return sent;
    }

    @Override
    public int send(byte[] pack) {
        // try to send data
        IOError error = null;
        int sent = -1;
        try {
            // prepare buffer
            ByteBuffer buffer = ByteBuffer.allocate(pack.length);
            buffer.put(pack);
            buffer.flip();
            // send buffer
            SocketAddress destination = getRemoteAddress();
            sent = send(buffer, destination);
            if (sent < 0) {  // == -1
                throw new IOException("failed to send data: " + pack.length + " byte(s) to " + destination);
            }
        } catch (IOException e) {
            //e.printStackTrace();
            error = new IOError(e);
            // socket error, close current channel
            setChannel(null);
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            if (error == null) {
                delegate.onConnectionSent(sent, pack, this);
            } else {
                delegate.onConnectionFailed(error, pack, this);
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
    public void tick(long now, long delta) {
        StateMachine machine = getStateMachine();
        if (machine != null) {
            machine.tick(now, delta);
        }
    }

    //
    //  Timed
    //

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
        return now <= lastSentTime + EXPIRES;
    }
    @Override
    public boolean isReceivedRecently(long now) {
        return now <= lastReceivedTime + EXPIRES;
    }
    @Override
    public boolean isNotReceivedLongTimeAgo(long now) {
        return now > lastReceivedTime + (EXPIRES << 3);
    }

    //
    //  Events
    //

    @Override
    public void enterState(ConnectionState next, StateMachine ctx, long now) {

    }

    @Override
    public void exitState(ConnectionState previous, StateMachine ctx, long now) {
        ConnectionState current = ctx.getCurrentState();
        // if current == 'ready'
        if (current != null && current.equals(ConnectionState.READY)) {
            // if previous == 'preparing'
            if (previous != null && previous.equals(ConnectionState.PREPARING)) {
                // connection state changed from 'preparing' to 'ready',
                // set times to expired soon.
                long timestamp = now - (EXPIRES >> 1);
                if (lastSentTime < timestamp) {
                    lastSentTime = timestamp;
                }
                if (lastReceivedTime < timestamp) {
                    lastReceivedTime = timestamp;
                }
            }
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionStateChanged(previous, current, this);
        }
    }

    @Override
    public void pauseState(ConnectionState current, StateMachine ctx, long now) {

    }

    @Override
    public void resumeState(ConnectionState current, StateMachine ctx, long now) {

    }
}
