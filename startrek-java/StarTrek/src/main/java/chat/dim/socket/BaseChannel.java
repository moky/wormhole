/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
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

import java.io.IOException;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.ByteChannel;
import java.nio.channels.NetworkChannel;
import java.nio.channels.SelectableChannel;

import chat.dim.net.Channel;
import chat.dim.net.SocketHelper;
import chat.dim.type.AddressPairObject;

public abstract class BaseChannel<C extends SelectableChannel>
        extends AddressPairObject
        implements Channel {

    // socket reader/writer
    protected final SocketReader reader;
    protected final SocketWriter writer;

    // inner socket
    private C impl;
    private int flag;  // closed flag
                       //   -1: initialized
                       //    0: false
                       //    1: true

    /**
     *  Create channel
     *
     * @param remote      - remote address
     * @param local       - local address
     */
    protected BaseChannel(SocketAddress remote, SocketAddress local) {
        super(remote, local);
        reader = createReader();
        writer = createWriter();
        impl = null;
        flag = -1;
    }

    @Override
    protected void finalize() throws Throwable {
        // make sure the relative socket is removed
        setSocketChannel(null);
        super.finalize();
    }

    /**
     *  Create socket reader
     */
    protected abstract SocketReader createReader();

    /**
     *  Create socket writer
     */
    protected abstract SocketWriter createWriter();

    //
    //  Socket
    //

    public C getSocketChannel() {
        return impl;
    }

    /**
     *  Set inner socket for this channel
     */
    public void setSocketChannel(C sock) {
        // 1. replace with new socket
        C old = impl;
        if (sock != null) {
            impl = sock;
            flag = 0;
        } else {
            impl = null;
            flag = 1;
        }
        // 2. close old socket
        if (old != null && old != sock) {
            SocketHelper.socketDisconnect(old);
        }
    }

    //
    //  States
    //

    @Override
    public Status getStatus() {
        if (flag < 0) {
            // initializing
            return Status.INIT;
        }
        C sock = impl;
        if (sock == null || !SocketHelper.socketIsOpen(sock)) {
            // closed
            return Status.CLOSED;
        } else if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
            // normal
            return Status.ALIVE;
        } else {
            // opened
            return Status.OPEN;
        }
    }

    @Override
    public boolean isOpen() {
        if (flag < 0) {
            // initializing, it is not 'closed'
            return true;
        }
        C sock = impl;
        return sock != null && SocketHelper.socketIsOpen(sock);
    }

    @Override
    public boolean isBound() {
        C sock = impl;
        return sock != null && SocketHelper.socketIsBound(sock);
    }

    @Override
    public boolean isConnected() {
        C sock = impl;
        return sock != null && SocketHelper.socketIsConnected(sock);
    }

    @Override
    public boolean isAlive() {
        return isOpen() && (isConnected() || isBound());
    }

    @Override
    public boolean isAvailable() {
        C sock = impl;
        if (sock != null && SocketHelper.socketIsOpen(sock)) {
            if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
                // alive, check reading buffer
                return checkAvailable(sock);
            }
        }
        return false;
    }

    protected boolean checkAvailable(C sock) {
        return SocketHelper.socketIsAvailable(sock);
    }

    @Override
    public boolean isVacant() {
        C sock = impl;
        if (sock != null && SocketHelper.socketIsOpen(sock)) {
            if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
                // alive, check writing buffer
                return checkVacant(sock);
            }
        }
        return false;
    }

    protected boolean checkVacant(C sock) {
        return SocketHelper.socketIsVacant(sock);
    }

    @Override
    public boolean isBlocking() {
        C sock = impl;
        return sock != null && SocketHelper.socketIsBlocking(sock);
    }

    @Override
    public SelectableChannel configureBlocking(boolean block) throws IOException {
        C sock = getSocketChannel();
        if (sock != null) {
            sock.configureBlocking(block);
        }
        return sock;
    }

    @Override
    public String toString() {
        String cname = getClass().getName();
        return "<" + cname + " remote=\"" + getRemoteAddress() + "\" local=\"" + getLocalAddress() + "\"" +
                " closed=" + (!isOpen()) + " bound=" + isBound() + " connected=" + isConnected() + ">\n\t"
                + impl + "\n</" + cname + ">";
    }

    protected boolean bind(C sock, SocketAddress local) {
        if (sock instanceof NetworkChannel) {
            return SocketHelper.socketBind((NetworkChannel) sock, local);
        }
        assert false : "socket error: " + sock;
        return false;
    }

    protected boolean connect(C sock, SocketAddress remote) {
        if (sock instanceof NetworkChannel) {
            return SocketHelper.socketConnect((NetworkChannel) sock, remote);
        }
        assert false : "socket error: " + sock;
        return false;
    }

    protected boolean disconnect(C sock) {
        return SocketHelper.socketDisconnect(sock);
    }

    @Override
    public NetworkChannel bind(SocketAddress local) throws IOException {
        if (local == null) {
            local = localAddress;
            assert local != null : "local address not set";
        }
        C sock = getSocketChannel();
        boolean ok = sock != null && bind(sock, local);
        if (!ok) {
            throw new SocketException("failed to bind socket: " + local);
        }
        localAddress = local;
        return (NetworkChannel) sock;
    }

    @Override
    public NetworkChannel connect(SocketAddress remote) throws IOException {
        if (remote == null) {
            remote = remoteAddress;
            assert remote != null : "remote address not set";
        }
        C sock = getSocketChannel();
        boolean ok = sock != null && connect(sock, remote);
        if (!ok) {
            throw new SocketException("failed to connect socket: " + remote);
        }
        remoteAddress = remote;
        return (NetworkChannel) sock;
    }

    @Override
    public ByteChannel disconnect() throws IOException {
        C sock = impl;
        boolean ok = sock == null || disconnect(sock);
        if (!ok) {
            throw new SocketException("failed to disconnect socket: " + sock);
        }
        // remoteAddress = null;
        return sock instanceof ByteChannel ? (ByteChannel) sock : null;
    }

    @Override
    public void close() throws IOException {
        setSocketChannel(null);
    }

    //
    //  Input/Output
    //

    @Override
    public int read(ByteBuffer dst) throws IOException {
        try {
            return reader.read(dst);
        } catch (IOException e) {
            close();
            throw e;
        }
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        try {
            return writer.write(src);
        } catch (IOException e) {
            close();
            throw e;
        }
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        try {
            return reader.receive(dst);
        } catch (IOException e) {
            close();
            throw e;
        }
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        try {
            return writer.send(src, target);
        } catch (IOException e) {
            close();
            throw e;
        }
    }

}
