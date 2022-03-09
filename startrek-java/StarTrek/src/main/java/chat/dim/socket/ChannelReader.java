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
import java.nio.ByteBuffer;
import java.nio.channels.ReadableByteChannel;
import java.nio.channels.SelectableChannel;

import chat.dim.net.BaseChannel;
import chat.dim.net.SocketReader;

public abstract class ChannelReader<C extends SelectableChannel>
        extends Controller<C> implements SocketReader {

    protected ChannelReader(BaseChannel<C> channel) {
        super(channel);
    }

    // 1. check timeout
    //    in blocking mode, the socket will wait until received something,
    //    but if timeout was set, it will return nothing too, it's normal;
    //    otherwise, we know the connection was lost.
    protected abstract IOException checkData(ByteBuffer buf, int len, C sock);

    protected int tryRead(ByteBuffer dst, C sock) throws IOException {
        try {
            return ((ReadableByteChannel) sock).read(dst);
        } catch (IOException e) {
            e = checkError(e, sock);
            if (e != null) {
                // connection lost?
                throw e;
            }
            // received nothing
            return -1;
        }
    }

    @Override
    public int read(ByteBuffer dst) throws IOException {
        C sock = getSocket();
        assert sock instanceof ReadableByteChannel : "socket error, cannot read data: " + sock;
        int cnt = tryRead(dst, sock);
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
