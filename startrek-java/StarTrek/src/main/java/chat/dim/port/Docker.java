/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.port;

import chat.dim.skywalker.Processor;

import java.net.SocketAddress;

/**
 *  Star Worker
 *  ~~~~~~~~~~~
 *
 *  Processor for Star Ships
 */
public interface Docker extends Processor {

    SocketAddress getLocalAddress();
    SocketAddress getRemoteAddress();

    /**
     *  Pack the payload to an outgo Ship
     *
     * @param payload     - request data
     * @param priority    - smaller is faster (-1 is the most fast)
     * @param delegate    - callback handler for the departure ship
     * @return departure ship containing payload
     */
    Departure pack(byte[] payload, int priority, Ship.Delegate delegate);

    /**
     *  Called when received data
     *
     * @param data   - received data package
     */
    void processReceived(byte[] data);

    /**
     *  Send 'PING' for keeping connection alive
     */
    void heartbeat();

    /**
     *  Clear all expired tasks
     */
    void purge();
}
