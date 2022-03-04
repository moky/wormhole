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
import java.net.SocketException;
import java.nio.ByteBuffer;
import java.nio.channels.SelectableChannel;
import java.nio.channels.WritableByteChannel;

import chat.dim.net.BaseChannel;

public abstract class ChannelWriter<C extends SelectableChannel>
        extends Controller<C> implements Writer {

    protected ChannelWriter(BaseChannel<C> channel) {
        super(channel);
    }

    protected int trySend(ByteBuffer buf, C sock) throws IOException {
        try {
            return ((WritableByteChannel) sock).write(buf);
        } catch (IOException error) {
            error = checkError(error, sock);
            if (error == null) {
                // buffer overflow!
                return -1;
            } else {
                // connection lost?
                throw error;
            }
        }
    }

    @Override
    public int write(ByteBuffer src) throws IOException {
        C sock = getSocket();
        if (!(sock instanceof WritableByteChannel)) {
            throw new SocketException("socket lost, cannot write data: " + src.position() + " byte(s)");
        }
        int sent = 0;
        int rest = src.position();
        int cnt;
        while (true) {  // while (sock.isOpen())
            cnt = trySend(src, sock);
            // check send result
            if (cnt == 0) {
                // buffer overflow?
                break;
            } else if (cnt < 0) {
                // buffer overflow!
                if (sent == 0) {
                    return -1;
                }
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
        return sent;
    }
}
