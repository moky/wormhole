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

import chat.dim.mem.BytesArray;
import chat.dim.tcp.Connection;

public class TCPGate extends StarGate implements Connection.Delegate {

    public final Connection connection;

    public TCPGate(Connection conn) {
        super();
        connection = conn;
    }

    @Override
    protected Docker createDocker() {
        // TODO: override to customize Worker
        if (MTPDocker.check(this)) {
            return new MTPDocker(this);
        }
        return null;
    }

    @Override
    public boolean isRunning() {
        // 1. StarGate not stopped
        // 2. Connection not closed or still have data unprocessed
        return super.isRunning() && (connection.isAlive() || connection.available() > 0);
    }

    @Override
    public boolean isExpired() {
        return connection.getStatus().equals(Connection.Status.Expired);
    }

    @Override
    public Status getStatus() {
        return getStatus(connection.getStatus());
    }

    //
    //  Connection Status -> Gate Status
    //
    public static Status getStatus(Connection.Status status) {
        switch (status) {
            case Connecting:
                return Status.Connecting;
            case Connected:
            case Maintaining:
            case Expired:
                return Status.Connected;
            case Error:
                return Status.Error;
            default:
                return Status.Init;
        }
    }

    @Override
    public boolean send(byte[] pack) {
        if (connection.isAlive()) {
            return connection.send(pack) == pack.length;
        } else {
            return false;
        }
    }

    @Override
    public byte[] receive(int length, boolean remove) {
        byte[] fragment = receive(length);
        if (fragment != null) {
            if (fragment.length > length) {
                if (remove) {
                    // fragment[length:]
                    chunks = BytesArray.slice(fragment, length);
                }
                // fragment[:length]
                return BytesArray.slice(fragment, 0, length);
            } else if (remove) {
                //assert fragment.length == length : "fragment length error";
                chunks = null;
            }
        }
        return fragment;
    }

    private byte[] chunks = null;

    private byte[] receive(int length) {
        int cached = 0;
        if (chunks != null) {
            cached = chunks.length;
        }
        int available;
        byte[] data;
        while (cached < length) {
            // check available length from connection
            available = connection.available();
            if (available <= 0) {
                break;
            }
            // try to receive data from connection
            data = connection.receive(available);
            if (data == null || data.length == 0) {
                break;
            }
            // append data
            if (chunks == null) {
                chunks = data;
            } else {
                chunks = BytesArray.concat(chunks, data);
            }
            cached += data.length;
        }
        return chunks;
    }

    //
    //  ConnectionHandler
    //

    @Override
    public void onConnectionStatusChanged(Connection connection, Connection.Status oldStatus, Connection.Status newStatus) {
        Status s1 = getStatus(oldStatus);
        Status s2 = getStatus(newStatus);
        if (!s1.equals(s2)) {
            Delegate delegate = getDelegate();
            if (delegate != null) {
                delegate.onStatusChanged(this, s1, s2);
            }
        }
    }

    @Override
    public void onConnectionReceivedData(Connection connection, byte[] data) {
        // received data will be processed in run loop,
        // do nothing here
    }
}
