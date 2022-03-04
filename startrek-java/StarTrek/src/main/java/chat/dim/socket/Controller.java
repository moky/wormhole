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
import java.nio.channels.SelectableChannel;

import chat.dim.net.BaseChannel;

public abstract class Controller<C extends SelectableChannel> {

    private final WeakReference<BaseChannel<C>> channelRef;

    protected Controller(BaseChannel<C> channel) {
        super();
        channelRef = new WeakReference<>(channel);
    }

    public BaseChannel<C> getChannel() {
        return channelRef.get();
    }

    public SocketAddress getRemoteAddress() {
        return getChannel().getRemoteAddress();
    }
    public SocketAddress getLocalAddress() {
        return getChannel().getLocalAddress();
    }

    public C getSocket() {
        BaseChannel<C> channel = getChannel();
        C sock = channel.getSocketChannel();
        if (sock == null) {
            throw new NullPointerException("socket lost: " + channel);
        }
        return sock;
    }

    // 1. check E_AGAIN
    //    the socket will raise 'Resource temporarily unavailable'
    //    when received nothing in non-blocking mode,
    //    or buffer overflow while sending too many bytes,
    //    here we should ignore this exception.
    // 2. check timeout
    //    in blocking mode, the socket will wait until send/received data,
    //    but if timeout was set, it will raise 'timeout' error on timeout,
    //    here we should ignore this exception
    protected abstract IOException checkError(IOException error, C sock);
}
