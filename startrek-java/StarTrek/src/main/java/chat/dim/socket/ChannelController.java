/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2022 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2022 Albert Moky
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
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.SelectableChannel;

import chat.dim.net.SocketHelper;

/**
 *  Socket Channel Controller
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 *  Reader, Writer, ErrorChecker
 */
abstract class ChannelController<C extends SelectableChannel> {

    private final WeakReference<BaseChannel<C>> channelRef;

    protected ChannelController(BaseChannel<C> channel) {
        super();
        channelRef = new WeakReference<>(channel);
    }

    public BaseChannel<C> getChannel() {
        return channelRef.get();
    }

    public SocketAddress getRemoteAddress() {
        BaseChannel<C> sock = getChannel();
        return sock == null ? null : sock.getRemoteAddress();
    }
    public SocketAddress getLocalAddress() {
        BaseChannel<C> sock = getChannel();
        return sock == null ? null : sock.getLocalAddress();
    }

    public C getSocket() {
        BaseChannel<C> sock = getChannel();
        return sock == null ? null : sock.getSocketChannel();
    }

    // TODO: override for receiving
    protected int receivePackage(SelectableChannel sock, ByteBuffer dst) throws IOException {
        if (sock == null || !sock.isOpen()) {
            throw new SocketException();
        }
        return SocketHelper.socketReceive(sock, dst);
    }

    // TODO: override for sending
    protected int sendAll(SelectableChannel sock, ByteBuffer src) throws IOException {
        if (sock == null || !sock.isOpen()) {
            throw new SocketException();
        }
        int sent = 0;
        int rest = src.position();
        int cnt;
        while (true) {  // while (sock.isOpen())
            cnt = SocketHelper.socketSend(sock, src);
            // check send result
            if (cnt <= 0) {
                // buffer overflow?
                break;
            }
            // something sent, check remaining data
            sent += cnt;
            rest -= cnt;
            if (rest <= 0) {
                // done!
                break;
            //} else {
            //    // remove sent part
            }
        }
        // OK
        if (sent > 0) {
            return sent;
        } else  if (cnt < 0) {
            assert cnt == -1 : "sent error: " + cnt;
            return -1;
        } else {
            return  0;
        }
    }

}
