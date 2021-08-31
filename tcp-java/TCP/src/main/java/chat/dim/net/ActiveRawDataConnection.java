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
package chat.dim.net;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.util.Arrays;

public abstract class ActiveRawDataConnection extends ActiveConnection<byte[]> {

    public ActiveRawDataConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super(byteChannel, remote, local);
    }

    public ActiveRawDataConnection(SocketAddress remote, SocketAddress local) {
        super(remote, local);
    }

    @Override
    public int send(byte[] pack, SocketAddress destination) throws IOException {
        ByteBuffer buffer = ByteBuffer.allocate(pack.length);
        buffer.put(pack);
        buffer.flip();
        return send(buffer, destination);
    }

    @Override
    public void heartbeat() throws IOException {
        send(PING, getRemoteAddress());
    }

    @Override
    protected byte[] parse(byte[] data, SocketAddress remote) {
        if (data.length < 6) {
            if (Arrays.equals(data, PING)) {
                // PING -> PONG
                try {
                    send(PONG, remote);
                } catch (IOException e) {
                    e.printStackTrace();
                }
                return null;
            } else if (Arrays.equals(data, PONG) ||
                    Arrays.equals(data, NOOP) ||
                    Arrays.equals(data, OK)) {
                // ignore them
                return null;
            }
        }
        return data;
    }
}
