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
import java.util.Date;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.ConnectionStateMachine;
import chat.dim.net.Hub;
import chat.dim.net.TimedConnection;
import chat.dim.type.AddressPairObject;
import chat.dim.type.Duration;

public class BaseConnection extends AddressPairObject
        implements Connection, TimedConnection, ConnectionState.Delegate {

    private WeakReference<Delegate> delegateRef = null;

    private WeakReference<Channel> channelRef = null;

    // active times
    private Date lastSentTime = null;
    private Date lastReceivedTime = null;

    // connection state machine
    private ConnectionStateMachine fsm = null;

    public BaseConnection(SocketAddress remote, SocketAddress local) {
        super(remote, local);
    }

    @Override
    protected void finalize() throws Throwable {
        // make sure the relative channel is closed
        setChannel(null);
        setStateMachine(null);
        super.finalize();
    }

    // delegate for handling connection events
    public void setDelegate(Delegate gate) {
        delegateRef = gate == null ? null : new WeakReference<>(gate);
    }
    protected Delegate getDelegate() {
        WeakReference<Delegate> ref = delegateRef;
        return ref == null ? null : ref.get();
    }

    //
    //  State Machine
    //

    protected ConnectionStateMachine getStateMachine() {
        return fsm;
    }
    private void setStateMachine(ConnectionStateMachine newMachine) {
        // 1. replace with new machine
        ConnectionStateMachine oldMachine = fsm;
        fsm = newMachine;
        // 2. stop old machine
        if (oldMachine != null && oldMachine != newMachine) {
            oldMachine.stop();
        }
    }
    protected ConnectionStateMachine createStateMachine() {
        ConnectionStateMachine machine = new ConnectionStateMachine(this);
        machine.setDelegate(this);
        return machine;
    }

    //
    //  Channel
    //

    protected Channel getChannel() {
        WeakReference<Channel> ref = channelRef;
        return ref == null ? null : ref.get();
    }
    protected void setChannel(Channel sock) {
        // 1. replace with new channel
        Channel old = getChannel();
        if (sock != null) {
            channelRef = new WeakReference<>(sock);
        } else {
            channelRef.clear();
            // channelRef = null;
        }
        // 2. close old channel
        if (old != null && old != sock) {
            try {
                old.close();
            } catch (IOException e) {
                /*/
                Delegate delegate = getDelegate();
                if (delegate != null) {
                    delegate.onConnectionError(new IOError(e), this);
                }
                /*/
            }
        }
    }

    @Override
    public boolean isOpen() {
        if (channelRef == null) {
            // initializing
            return true;
        }
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

    @Override
    public boolean isAvailable() {
        Channel sock = getChannel();
        return sock != null && sock.isAvailable();
    }

    @Override
    public boolean isVacant() {
        Channel sock = getChannel();
        return sock != null && sock.isVacant();
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
                + getChannel() + "\n</" + cname + ">";
    }

    @Override
    public void close() {
        // stop state machine
        setStateMachine(null);
        // close channel
        setChannel(null);
    }

    // Get channel from hub
    public void start(Hub hub) {
        // 1. get channel from hub
        openChannel(hub);
        // 2. start state machine
        startMachine();
    }

    protected void startMachine() {
        ConnectionStateMachine machine = createStateMachine();
        setStateMachine(machine);
        machine.start();
    }

    protected Channel openChannel(Hub hub) {
        Channel sock = hub.open(remoteAddress, localAddress);
        if (sock == null) {
            assert false : "failed to open channel: remote=" + remoteAddress + ", local=" + localAddress;
        } else {
            setChannel(sock);
        }
        return sock;
    }

    //
    //  I/O
    //

    @Override
    public void onReceivedData(byte[] data) {
        lastReceivedTime = new Date();  // update received time
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionReceived(data, this);
        }
    }

    protected int send(ByteBuffer src, SocketAddress destination) throws IOException {
        Channel sock = getChannel();
        if (sock == null || !sock.isAlive()) {
            assert false : "socket channel lost: " + sock;
            return -1;
        } else if (destination == null) {
            assert false : "remote address should not empty";
            return -1;
        }
        int sent = sock.send(src, destination);
        if (sent > 0) {
            // update sent time
            lastSentTime = new Date();
        }
        return sent;
    }

    @Override
    public int sendData(byte[] pack) {
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
        ConnectionStateMachine machine = getStateMachine();
        return machine == null ? null : machine.getCurrentState();
    }

    @Override
    public void tick(Date now, Duration delta) {
        if (channelRef == null) {
            // not initialized
            return;
        }
        ConnectionStateMachine machine = getStateMachine();
        if (machine != null) {
            // drive state machine forward
            machine.tick(now, delta);
        }
    }

    //
    //  Timed
    //

    @Override
    public Date getLastSentTime() {
        return lastSentTime;
    }

    @Override
    public Date getLastReceivedTime() {
        return lastReceivedTime;
    }

    @Override
    public boolean isSentRecently(Date now) {
        Date last = lastSentTime;
        if (last == null) {
            return false;
        }
        assert now != null : "should not happen";
        //return now.getTime() <= last.getTime() + EXPIRES;
        return EXPIRES.addTo(last).after(now);
    }
    @Override
    public boolean isReceivedRecently(Date now) {
        Date last = lastReceivedTime;
        if (last == null) {
            return false;
        }
        assert now != null : "should not happen";
        //return now.getTime() <= last.getTime() + EXPIRES;
        return EXPIRES.addTo(last).after(now);
    }
    @Override
    public boolean isNotReceivedLongTimeAgo(Date now) {
        Date last = lastReceivedTime;
        if (last == null) {
            return true;
        }
        assert now != null : "should not happen";
        //return now.getTime() > last.getTime() + (EXPIRES << 3);
        return EXPIRES.multiply(8).addTo(last).before(now);
    }

    //
    //  Events
    //

    @Override
    public void enterState(ConnectionState next, ConnectionStateMachine ctx, Date now) {

    }

    @Override
    public void exitState(ConnectionState previous, ConnectionStateMachine ctx, Date now) {
        ConnectionState current = ctx.getCurrentState();
        // if current == 'ready'
        if (current != null && current.equals(ConnectionState.Order.READY)) {
            // if previous == 'preparing'
            if (previous != null && previous.equals(ConnectionState.Order.PREPARING)) {
                // connection state changed from 'preparing' to 'ready',
                // set times to expired soon.
                assert now != null : "should not happen";
                //long soon = now.getTime() - (EXPIRES >> 1);
                Date soon = EXPIRES.divide(2).subtractFrom(now);
                Date st = lastSentTime;
                if (st == null || st.before(soon)) {
                    lastSentTime = soon;
                }
                Date rt = lastReceivedTime;
                if (rt == null || rt.before(soon)) {
                    lastReceivedTime = soon;
                }
            }
        }
        // callback
        Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onConnectionStateChanged(previous, current, this);
        }
        // if current == 'error'
        if (current != null && current.equals(ConnectionState.Order.ERROR)) {
            // remove channel when error
            setChannel(null);
        }
    }

    @Override
    public void pauseState(ConnectionState current, ConnectionStateMachine ctx, Date now) {

    }

    @Override
    public void resumeState(ConnectionState current, ConnectionStateMachine ctx, Date now) {

    }

}
