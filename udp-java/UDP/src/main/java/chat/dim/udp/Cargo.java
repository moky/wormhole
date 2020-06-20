/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2019 Albert Moky
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
package chat.dim.udp;

import java.net.DatagramPacket;
import java.net.SocketAddress;

public class Cargo {

    public final byte[] data;
    public final SocketAddress source;
    public SocketAddress destination;

    public Cargo(byte[] data, SocketAddress source, SocketAddress destination) {
        super();
        this.data = data;
        this.source = source;
        this.destination = destination;
    }

    public Cargo(byte[] data, SocketAddress source) {
        this(data, source, null);
    }

    public Cargo(DatagramPacket packet, Socket socket) {
        this(getData(packet), packet.getSocketAddress(), socket.localAddress);
    }

    public Cargo(DatagramPacket packet) {
        this(getData(packet), packet.getSocketAddress(), null);
    }

    private static byte[] getData(DatagramPacket packet) {
        byte[] data = packet.getData();
        int offset = packet.getOffset();
        int length = packet.getLength();
        if (offset == 0 && length == data.length) {
            return data;
        }
        byte[] buffer = new byte[length];
        System.arraycopy(data, offset, buffer, 0, length);
        return buffer;
    }
}
