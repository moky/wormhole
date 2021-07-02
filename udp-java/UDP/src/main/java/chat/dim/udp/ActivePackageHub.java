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
import java.lang.ref.WeakReference;
import java.net.SocketAddress;

import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.PackageConnection;

public class ActivePackageHub extends BaseHub {

    private final WeakReference<Connection.Delegate> delegateRef;

    public ActivePackageHub(Connection.Delegate delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
    }

    public Connection.Delegate getDelegate() {
        return delegateRef.get();
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        PackageConnection connection = new PackageConnection(remote, local) {
            @Override
            protected Channel connect(SocketAddress remote, SocketAddress local) throws IOException {
                return new DiscreteChannel(remote, local);
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

    @Override
    public byte[] receive(SocketAddress source, SocketAddress destination) {
        try {
            Connection conn = getConnection(source, destination);
            if (conn instanceof PackageConnection) {
                return ((PackageConnection) conn).receive(source, destination);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            Connection conn = getConnection(destination, source);
            if (conn instanceof PackageConnection) {
                return ((PackageConnection) conn).send(data, source, destination);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return -1;
    }
}
