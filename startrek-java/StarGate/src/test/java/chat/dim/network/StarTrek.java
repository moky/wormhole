/* license: https://mit-license.org
 *
 *  Star Gate: Interfaces for network connection
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
package chat.dim.network;

import java.net.Socket;

import chat.dim.stargate.Docker;
import chat.dim.stargate.StarGate;
import chat.dim.tcp.ActiveConnection;
import chat.dim.tcp.BaseConnection;

public class StarTrek extends StarGate {

    private final BaseConnection baseConnection;

    public StarTrek(BaseConnection conn) {
        super(conn);
        baseConnection = conn;
    }

    private static StarGate createGate(Socket socket) {
        BaseConnection conn = new BaseConnection(socket);
        StarGate gate = new StarTrek(conn);
        conn.setDelegate(gate);
        return gate;
    }
    private static StarGate createGate(String host, int port) {
        ActiveConnection conn = new ActiveConnection(host, port);
        StarGate gate = new StarTrek(conn);
        conn.setDelegate(gate);
        return gate;
    }
    private static StarGate createGate(String host, int port, Socket socket) {
        ActiveConnection conn = new ActiveConnection(host, port, socket);
        StarGate gate = new StarTrek(conn);
        conn.setDelegate(gate);
        return gate;
    }

    @Override
    protected Docker createDocker() {
        if (MTPDocker.check(connection)) {
            return new MTPDocker(this);
        }
        return null;
    }

    @Override
    public void setup() {
        new Thread(baseConnection).start();
        super.setup();
    }

    @Override
    public void finish() {
        super.finish();
        baseConnection.stop();
    }
}
