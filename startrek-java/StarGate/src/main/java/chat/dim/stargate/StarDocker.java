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
import java.util.Date;

public abstract class StarDocker implements Docker, Runnable {

    private final WeakReference<Gate> gateRef;

    private boolean running;
    private long heartbeatExpired;

    public StarDocker(Gate gate) {
        super();
        gateRef = new WeakReference<>(gate);
        running = false;
        // time for checking heartbeat
        heartbeatExpired = (new Date()).getTime() + 2000;
    }

    public Gate getGate() {
        return gateRef.get();
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

    public boolean isWorking() {
        return running && getGate().isOpened();
    }

    @Override
    public void setup() {
        running = true;
    }

    @Override
    public void finish() {
        // TODO: go through all outgo Ships parking in Dock and call 'sent failed' on their delegates
        running = false;
    }

    @Override
    public void handle() {
        while (isWorking()) {
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
        // 1. process income
        Ship income = getIncomeShip();
        if (income != null) {
            // 1.1. remove linked package
            removeLinkedShip(income);
            // 1.2. process income package
            StarShip res = processIncomeShip(income);
            if (res != null) {
                // if res.priority < 0, send the response immediately;
                // or, put this ship into a waiting queue.
                getGate().send(res);
            }
        }
        // 2. process outgo
        StarShip outgo = getOutgoShip();
        if (outgo != null) {
            if (outgo.isExpired()) {
                // outgo Ship expired, callback
                Ship.Delegate delegate = outgo.getDelegate();
                if (delegate != null) {
                    delegate.onSent(outgo, new Gate.Error(outgo, "Request timeout"));
                }
            } else if (!getGate().send(outgo.getPackage())) {
                // failed to send outgo package, callback
                Ship.Delegate delegate = outgo.getDelegate();
                if (delegate != null) {
                    delegate.onSent(outgo, new Gate.Error(outgo, "Connection error"));
                }
            }
        }
        // 3. heartbeat
        if (income == null && outgo == null) {
            // check time for next heartbeat
            long now = (new Date()).getTime();
            if (now > heartbeatExpired) {
                if (getGate().isExpired()) {
                    StarShip beat = getHeartbeat();
                    if (beat != null) {
                        // put the heartbeat into waiting queue
                        getGate().parkShip(beat);
                    }
                }
                // try heartbeat next 2 seconds
                heartbeatExpired = now + 2000;
            }
            return false;
        } else {
            return true;
        }
    }

    /**
     *  Get income Ship from Connection
     */
    protected abstract Ship getIncomeShip();

    /**
     *  Process income Ship
     */
    protected abstract StarShip processIncomeShip(Ship income);

    protected void removeLinkedShip(Ship income) {
        StarShip linked = getOutgoShip(income);
        if (linked != null) {
            // callback for the linked outgo Ship and remove it
            Ship.Delegate delegate = linked.getDelegate();
            if (delegate != null) {
                delegate.onSent(linked, null);
            }
        }
    }

    /**
     *  Get outgo Ship from waiting queue
     */
    protected StarShip getOutgoShip() {
        // get next new task (time == 0)
        StarShip outgo = getGate().pullShip();
        if (outgo == null) {
            // no more new task now, get any expired task
            outgo = getGate().anyShip();
        }
        return outgo;
    }

    /**
     *  get task with ID (income.SN)
     */
    protected StarShip getOutgoShip(Ship income) {
        return getGate().pullShip(income.getSN());
    }

    /**
     *  Get an empty ship for keeping connection alive
     */
    protected StarShip getHeartbeat() {
        return null;
    }
}
