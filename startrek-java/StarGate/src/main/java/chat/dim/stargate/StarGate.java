/* license: https://mit-license.org
 *
 *  Star Gate: Interfaces for network connection
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
package chat.dim.stargate;

import java.lang.ref.WeakReference;

import chat.dim.mem.BytesArray;
import chat.dim.tcp.Connection;

public abstract class StarGate implements Gate, Connection.Delegate, Runnable {

    public final Dock dock;
    public final Connection connection;

    private Docker docker = null;
    private WeakReference<Delegate> delegateRef = null;

    private boolean running = false;

    public StarGate(Connection conn) {
        super();
        dock = createDock();
        connection = conn;
    }

    protected Dock createDock() {
        return new LockedDock();
    }

    public Docker getDocker() {
        if (docker == null) {
            docker = createDocker();
        }
        return docker;
    }

    // override to customize Worker
    protected abstract Docker createDocker();

    public void setDocker(Docker worker) {
        docker = worker;
    }

    @Override
    public Delegate getDelegate() {
        if (delegateRef == null) {
            return null;
        } else {
            return delegateRef.get();
        }
    }
    public void setDelegate(Delegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }

    @Override
    public boolean isOpened() {
        // 1. StarGate not stopped
        // 2. Connection not closed or still have data unprocessed
        return running && (connection.isAlive() || connection.available() > 0);
    }

    @Override
    public boolean isExpired() {
        return connection.getStatus().equals(Connection.Status.Expired);
    }

    @Override
    public Status getStatus() {
        return Gate.getStatus(connection.getStatus());
    }

    @Override
    public boolean send(byte[] payload, int priority, Ship.Delegate delegate) {
        Docker worker = getDocker();
        if (worker == null) {
            return false;
        } else {
            StarShip outgo = worker.pack(payload, priority, delegate);
            return send(outgo);
        }
    }

    @Override
    public boolean send(StarShip outgo) {
        if (outgo.priority <= StarShip.URGENT && getStatus().equals(Status.Connected)) {
            // send out directly
            return send(outgo.getPackage());
        } else {
            // put the Ship into a waiting queue
            return parkShip(outgo);
        }
    }

    //
    //  Connection
    //

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
    //  Docking
    //

    @Override
    public boolean parkShip(StarShip outgo) {
        return dock.put(outgo);
    }

    @Override
    public StarShip pullShip(byte[] sn) {
        return dock.pop(sn);
    }

    @Override
    public StarShip pullShip() {
        return dock.pop();
    }

    @Override
    public StarShip anyShip() {
        return dock.any();
    }

    //
    //  Running
    //

    @Override
    public void run() {
        setup();
        try {
            handle();
        } finally {
            finish();
        }
    }

    public void stop() {
        running = false;
    }

    public void setup() {
        running = true;
        if (!isOpened()) {
            // waiting for connection
            idle();
        }
        // check docker
        while (getDocker() == null && isOpened()) {
            // waiting for docker
            idle();
        }
        // setup docker
        if (docker != null) {
            docker.setup();
        }
    }

    public void finish() {
        running = false;
        // clean docker
        if (docker != null) {
            docker.finish();
        }
    }

    public void handle() {
        while (isOpened()) {
            if (!process()) {
                idle();
            }
        }
    }

    protected void idle() {
        try {
            Thread.sleep(128);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public boolean process() {
        if (docker == null) {
            //throw new NullPointerException("Star worker not found!");
            return false;
        } else {
            return docker.process();
        }
    }

    //
    //  ConnectionHandler
    //

    @Override
    public void onConnectionStatusChanged(Connection connection, Connection.Status oldStatus, Connection.Status newStatus) {
        Status s1 = Gate.getStatus(oldStatus);
        Status s2 = Gate.getStatus(newStatus);
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
