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
package chat.dim.net;

import java.io.IOException;
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.ReadableByteChannel;
import java.nio.channels.SelectableChannel;

public abstract class SocketChannelReader<C extends SelectableChannel> extends SocketChannelController<C>
        implements SocketReader {

    protected SocketChannelReader(BaseChannel<C> channel) {
        super(channel);
    }

    protected IOException checkData(ByteBuffer buf, int len, C sock) {
        // in blocking mode, the socket will wait until received something,
        // but if timeout was set, it will return nothing too, it's normal;
        // otherwise, we know the connection was lost.
        if (len == 0) {
            if (sock == null) {
                sock = getSocket();
            }
            // TODO: check timeout
        }

        // no error
        return null;
    }

    @Override
    public int read(ByteBuffer dst) throws IOException {
        C sock = getSocket();
        int cnt = -1;
        try {
            if (sock instanceof ReadableByteChannel) {
                cnt = ((ReadableByteChannel) sock).read(dst);
            }
            if (cnt < 0) {
                throw new SocketException("socket lost, cannot read data");
            }
        } catch (IOException error) {
            error = checkError(error, sock);
            if (error != null) {
                // connection lost?
                throw error;
            }
            // received nothing
            dst.clear();
            cnt = 0;
        }
        // check data
        IOException error = checkData(dst, cnt, sock);
        if (error != null) {
            // connection lost!
            throw error;
        }
        // OK
        return cnt;
    }
}
