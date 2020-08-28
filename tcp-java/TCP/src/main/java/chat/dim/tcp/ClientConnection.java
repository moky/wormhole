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
import java.net.InetSocketAddress;
import java.net.Socket;

public class ClientConnection extends Connection {

    public ClientConnection(String serverHost, int serverPort) {
        super(null,
                new InetSocketAddress(serverHost, serverPort),
                serverHost, serverPort);
    }

    private int connect() {
        if (socket != null) {
            // connected
            return 0;
        }
        setStatus(ConnectionStatus.Connecting);
        try {
            socket = new Socket(host, port);
            setStatus(ConnectionStatus.Connected);
            return 0;
        } catch (IOException e) {
            e.printStackTrace();
            setStatus(ConnectionStatus.Error);
            return -1;
        }
    }

    @Override
    protected byte[] read() {
        // 0. check current connection
        if (connect() < 0) {
            return null;
        }
        try {
            // 1. try to read from current connection
            return super.read();
        } catch (IOException e) {
            e.printStackTrace();
            socket = null;
        }
        // 2. try to reconnect
        _sleep(500);
        if (connect() < 0) {
            return null;
        }
        try {
            // 3. try to read from new connection
            return super.read();
        } catch (IOException e) {
            e.printStackTrace();
            socket = null;
        }
        // failed to read
        _sleep(200);
        return null;
    }

    @Override
    protected int write(byte[] data) {
        // 0. check current connection
        if (connect() < 0) {
            return -1;
        }
        try {
            // 1. try to read from current connection
            return super.write(data);
        } catch (IOException e) {
            e.printStackTrace();
            socket = null;
        }
        // 2. try to reconnect
        _sleep(500);
        if (connect() < 0) {
            return -1;
        }
        try {
            // 3. try to read from new connection
            return super.write(data);
        } catch (IOException e) {
            e.printStackTrace();
            socket = null;
        }
        // failed to read
        _sleep(200);
        return -1;
    }
}
