/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.startrek;

import java.net.Socket;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.tcp.ActiveConnection;
import chat.dim.tcp.BaseConnection;

public class StarTrek extends TCPGate {

    public StarTrek(BaseConnection conn) {
        super(conn);
    }

    private static StarGate createGate(BaseConnection conn) {
        StarTrek gate = new StarTrek(conn);
        conn.setDelegate(gate);
        return gate;
    }
    public static StarGate createGate(Socket socket) {
        return createGate(new BaseConnection(socket));
    }
    public static StarGate createGate(String host, int port) {
        return createGate(new ActiveConnection(host, port));
    }
    public static StarGate createGate(String host, int port, Socket socket) {
        return createGate(new ActiveConnection(host, port, socket));
    }

    private final ReadWriteLock sendLock = new ReentrantReadWriteLock();
    private final ReadWriteLock receiveLock = new ReentrantReadWriteLock();

    @Override
    public boolean send(byte[] pack) {
        boolean ok;
        Lock writeLock = sendLock.writeLock();
        writeLock.lock();
        try {
            ok = super.send(pack);
        } finally {
            writeLock.unlock();
        }
        return ok;
    }

    @Override
    public byte[] receive(int length, boolean remove) {
        byte[] data;
        Lock writeLock = receiveLock.writeLock();
        writeLock.lock();
        try {
            data = super.receive(length, remove);
        } finally {
            writeLock.unlock();
        }
        return data;
    }

    @Override
    public void setup() {
        new Thread(connection).start();
        super.setup();
    }

    @Override
    public void finish() {
        super.finish();
        connection.stop();
    }
}
