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

import java.lang.ref.WeakReference;
import java.net.SocketAddress;

import chat.dim.net.Channel;
import chat.dim.net.Hub;

/**
 * Active connection for client
 */
public class ActiveConnection extends BaseConnection {

    private final WeakReference<Hub> hubRef;

    public ActiveConnection(SocketAddress remote, SocketAddress local, Channel sock, Delegate delegate, Hub hub) {
        super(remote, local, sock, delegate);
        hubRef = new WeakReference<>(hub);
    }

    public Hub getHub() {
        return hubRef.get();
    }

    @Override
    public boolean isOpen() {
        return getStateMachine() != null;
    }

    @Override
    protected Channel getChannel() {
        Channel sock = super.getChannel();
        if (sock == null || !sock.isOpen()) {
            if (getStateMachine() == null) {
                // closed (not start yet)
                return null;
            }
            // get new channel via hub
            sock = getHub().open(remoteAddress, localAddress);
            assert sock != null : "failed to open channel: " + remoteAddress + ", " + localAddress;
            setChannel(sock);
        }
        return sock;
    }
}
