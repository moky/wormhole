/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
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
package chat.dim.tcp;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.channels.SocketChannel;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.socket.ActiveConnection;
import chat.dim.socket.BaseChannel;

/**
 *  Stream Client Hub
 *  ~~~~~~~~~~~~~~~~~
 */
public class ClientHub extends StreamHub {

    public ClientHub(Connection.Delegate gate) {
        super(gate);
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        ActiveConnection conn = new ActiveConnection(remote, local);
        conn.setDelegate(getDelegate());  // gate
        return conn;
    }

    @SuppressWarnings("unchecked")
    @Override
    public Channel open(SocketAddress remote, SocketAddress local) {
        if (remote == null) {
            assert false : "remote address empty";
            return null;
        }
        //
        //  1. check channel
        //
        Channel channel = getChannel(remote, local);
        if (channel != null) {
            return channel;
        }
        // channel not exists, create new one
        channel = createChannel(remote, local);
        if (local == null) {
            local = channel.getLocalAddress();
        }
        // cache the channel
        Channel cached = setChannel(remote, local, channel);
        if (cached != null && cached != channel) {
            closeChannel(cached);
        }
        //
        //  2. create socket
        //
        if (channel instanceof BaseChannel) {
            SocketChannel socket = createSocket(remote, local);
            if (socket == null) {
                // assert false : "failed to prepare socket: " + local + " -> " + remote;
                removeChannel(remote, local, channel);
                channel = null;
            } else {
                ((BaseChannel<SocketChannel>) channel).setSocket(socket);
            }
        }
        return channel;
    }

    private static SocketChannel createSocket(SocketAddress remote, SocketAddress local) {
        try {
            SocketChannel sock = SocketChannel.open();
            sock.configureBlocking(true);
            if (local != null) {
                sock.socket().setReuseAddress(false);
                sock.bind(local);
            }
            assert remote != null : "remote address empty";
            sock.connect(remote);
            sock.configureBlocking(false);
            return sock;
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

}
