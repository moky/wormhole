/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.startrek;

import java.lang.ref.WeakReference;

import chat.dim.skywalker.Runner;

public abstract class StarGate extends Runner implements Gate {

    public final Dock dock;

    private Docker docker;
    private WeakReference<Delegate> delegateRef;

    protected StarGate() {
        super();
        dock = createDock();
        docker = null;
        delegateRef = null;
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
        if (!getStatus().equals(Status.CONNECTED)) {
            // not connect yet
            return false;
        } else if (outgo.priority > StarShip.URGENT) {
            // put the Ship into a waiting queue
            return parkShip(outgo);
        } else {
            // send out directly
            return send(outgo.getPackage());
        }
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
    //  Runner
    //

    @Override
    public void setup() {
        super.setup();
        // check connection
        if (!isRunning()) {
            // wait a second for connecting
            idle();
        }
        // check docker
        while (getDocker() == null && isRunning()) {
            // waiting for docker
            idle();
        }
        // setup docker
        if (docker != null) {
            docker.setup();
        }
    }

    @Override
    public void finish() {
        // clean docker
        if (docker != null) {
            docker.finish();
        }
        super.finish();
    }

    @Override
    public boolean process() {
        if (docker == null) {
            //throw new NullPointerException("Star worker not found!");
            return false;
        } else {
            return docker.process();
        }
    }
}
