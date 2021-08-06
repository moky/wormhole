/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
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

/*
 *  Topology:
 *
 *                          +---------------+
 *                          |      APP      |
 *                          +---------------+
 *                              |       A
 *                              |       |
 *                              V       |
 *          +-----------------------------------------------+
 *          |                                               |
 *          |     +----------+     HUB     +----------+     |
 *          |     |  socket  |             |  socket  |     |
 *          +-----+----------+-------------+----------+-----+
 *                   |    A                   |  |  A
 *                   |    |   (connections)   |  |  |
 *                   |    |    (+channels)    |  |  |
 *                   |    |                   |  |  |
 *          ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
 *          ~~~~~~~~~|~~~~|~~~~~~~~~~~~~~~~~~~|~~|~~|~~~~~~~~
 *                   |    |                   |  |  |
 *                   V    |                   V  V  |
 */

import java.io.IOException;
import java.net.SocketAddress;

public interface Hub {

    /**
     *  Send data from source to destination
     *
     * @param data        - payload
     * @param source      - from address (local);
     *                      if it's null, send via any connection connected to destination
     * @param destination - to address (remote)
     * @return false on error
     */
    boolean send(byte[] data, SocketAddress source, SocketAddress destination) throws IOException;

    /**
     *   Get connection if already exists
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on connection not found
     */
    Connection getConnection(SocketAddress remote, SocketAddress local);

    /**
     *  Get/create connection
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on error
     */
    Connection connect(SocketAddress remote, SocketAddress local) throws IOException;

    /**
     *  Close connection
     *
     * @param remote - remote address
     * @param local  - local address
     */
    void disconnect(SocketAddress remote, SocketAddress local) throws IOException;
}
