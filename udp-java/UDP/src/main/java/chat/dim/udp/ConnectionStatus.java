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

public enum ConnectionStatus {

    Error     (-1),
    Default    (0),
    Connecting (1),
    Connected  (2);

    public final int value;

    ConnectionStatus(int value) {
        this.value = value;
    }

    public boolean equals(ConnectionStatus other) {
        return this.value == other.value;
    }

    public static ConnectionStatus evaluate(float now,
                                            float sendExpired,
                                            float receiveExpired,
                                            float connectionLost) {
        if (now < receiveExpired) {
            /*  When received a package from remote address, this node must respond
             *  a package, so 'send expired' is always late than 'receive expired'.
             *  So, if received anything (normal package or just 'PING') from this
             *  connection, this indicates 'Connected'.
             */
            return Connected;
        } else if (now > connectionLost) {
            /*  It's a long time to receive nothing (even a 'PONG'), this connection
             *  may be already lost, needs to reconnect again.
             */
            return Error;
        } else if (now < sendExpired) {
            /*  If sent package through this connection recently but not received
                anything yet (includes 'PONG'), this indicates 'Connecting'.
             */
            return Connecting;
        } else {
            /*  It's a long time to send nothing, this connection needs maintaining,
                send something immediately (e.g.: 'PING') to keep it alive.
             */
            return Default;
        }
    }
}
