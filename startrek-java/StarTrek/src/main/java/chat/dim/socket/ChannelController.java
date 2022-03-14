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
import java.nio.ByteBuffer;
import java.nio.channels.ClosedChannelException;
import java.nio.channels.SelectableChannel;

/**
 *  Socket Channel Controller
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 *  Reader, Writer, ErrorChecker
 */
abstract class ChannelController<C extends SelectableChannel> implements ChannelChecker<C> {

    private final WeakReference<BaseChannel<C>> channelRef;
    private final ChannelChecker<C> checker;

    protected ChannelController(BaseChannel<C> channel) {
        super();
        channelRef = new WeakReference<>(channel);
        checker = createChecker();
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
        return getChannel().getSocketChannel();
    }

    //
    //  Checker
    //

    @Override
    public IOException checkError(IOException error, C sock) {
        return checker.checkError(error, sock);
    }

    @Override
    public IOException checkData(ByteBuffer buf, int len, C sock) {
        return checker.checkData(buf, len, sock);
    }

    protected ChannelChecker<C> createChecker() {
        return new ChannelChecker<C>() {
            @Override
            public IOException checkError(IOException error, C sock) {
                // TODO: check 'E_AGAIN' & TimeoutException
                return error;
            }

            @Override
            public IOException checkData(ByteBuffer buf, int len, C sock) {
                // TODO: check Timeout for received nothing
                if (len == -1) {
                    return new ClosedChannelException();
                }
                return null;
            }
        };
    }
}
