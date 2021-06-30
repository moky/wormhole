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
package chat.dim.tcp;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;

import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;

public class ActiveHub extends BaseHub {

    private WeakReference<Connection.Delegate> delegateRef = null;

    public ActiveHub(Connection.Delegate delegate) {
        super();
        setDelegate(delegate);
    }

    public void setDelegate(Connection.Delegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }
    public Connection.Delegate getDelegate() {
        return delegateRef == null ? null : delegateRef.get();
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException {
        ActiveConnection connection = new ActiveConnection(remote) {
            @Override
            protected Channel connect(SocketAddress remote) throws IOException {
                Channel channel = new StreamChannel();
                channel.connect(remote);
                channel.configureBlocking(false);
                if (local != null) {
                    channel.bind(local);
                }
                return channel;
            }
        };
        // set delegate
        Connection.Delegate delegate = getDelegate();
        if (delegate != null) {
            connection.setDelegate(delegate);
        }
        // start FSM
        connection.start();
        // connect to remote address
        if (remote != null) {
            connection.connect(remote);
        }
        return connection;
    }
}
