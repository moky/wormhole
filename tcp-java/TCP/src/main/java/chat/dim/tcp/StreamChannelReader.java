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
package chat.dim.tcp;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.ClosedChannelException;
import java.nio.channels.SocketChannel;

import chat.dim.socket.BaseChannel;
import chat.dim.socket.ChannelReader;

public class StreamChannelReader extends ChannelReader<SocketChannel> {

    protected StreamChannelReader(BaseChannel<SocketChannel> channel) {
        super(channel);
    }

    @Override
    public SocketChannel getSocket() {
        return getChannel().getSocketChannel();
    }

    @Override
    protected IOException checkError(IOException error, SocketChannel sock) {
        // TODO: check 'E_AGAIN' & TimeoutException
        return error;
    }

    @Override
    protected IOException checkData(ByteBuffer buf, int len, SocketChannel sock) {
        // TODO: check Timeout for received nothing
        if (len == -1) {
            return new ClosedChannelException();
        }
        return null;
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        return read(dst) > 0 ? getRemoteAddress() : null;
    }
}
