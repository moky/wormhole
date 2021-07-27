/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.udp;

import java.io.IOException;
import java.net.SocketAddress;

import chat.dim.net.ActivePackageConnection;
import chat.dim.net.Channel;
import chat.dim.net.Connection;

public abstract class ActivePackageHub extends PackageHub {

    public ActivePackageHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        ActivePackageConnection connection = new ActivePackageConnection(remote, local) {
            @Override
            protected Channel connect(SocketAddress remote, SocketAddress local) throws IOException {
                return createChannel(remote, local);
            }
        };
        // set delegate
        if (connection.getDelegate() == null) {
            connection.setDelegate(getDelegate());
        }
        // start FSM
        connection.start();
        return connection;
    }

    protected abstract Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException;
}
