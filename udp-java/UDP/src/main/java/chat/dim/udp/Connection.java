/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.udp;

import java.net.SocketAddress;
import java.util.Date;

public class Connection {

    public static long EXPIRES = 28;  // seconds

    public final SocketAddress remoteAddress;
    public final SocketAddress localAddress;

    private float connectionLost;
    private float receiveExpired;
    private float sendExpired;

    public Connection(SocketAddress remoteAddress, SocketAddress localAddress) {
        super();
        this.localAddress = localAddress;
        this.remoteAddress = remoteAddress;
        // connecting time
        Date now = new Date();
        float timestamp = now.getTime() / 1000.0f;
        this.connectionLost = timestamp + (EXPIRES << 4);
        this.receiveExpired = timestamp; // + EXPIRES
        this.sendExpired = timestamp; // + EXPIRES
    }

    public ConnectionStatus getStatus(float timestamp) {
        return ConnectionStatus.evaluate(timestamp, sendExpired, receiveExpired, connectionLost);
    }

    public ConnectionStatus getStatus() {
        Date now = new Date();
        float timestamp = now.getTime() / 1000.0f;
        return getStatus(timestamp);
    }

    public void updateSentTime(float timestamp) {
        // update last send time
        sendExpired = timestamp + EXPIRES;
    }

    public void updateReceivedTime(float timestamp) {
        // update last receive time
        connectionLost = timestamp + (EXPIRES << 4);
        receiveExpired = timestamp + EXPIRES;
    }
}
