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

import java.net.SocketAddress;
import java.util.Date;
import java.util.List;

import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.port.Gate;

public abstract class StarDocker implements Docker {

    private final SocketAddress remoteAddress;

    private final Dock dock;

    protected StarDocker(SocketAddress remote) {
        super();
        remoteAddress = remote;
        dock = createDock();
    }

    protected Dock createDock() {
        return new LockedDock();
    }

    protected abstract Gate getGate();

    protected abstract Gate.Delegate getDelegate();

    private Gate.Status getStatus() {
        return getGate().getStatus(remoteAddress);
    }
    private boolean isConnected() {
        return getStatus().equals(Gate.Status.CONNECTED);
    }

    private void onError(String message, Departure ship) {
        Gate.Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onError(new Error(message), ship, remoteAddress, getGate());
        }
    }

    private boolean send(Departure outgo) {
        List<byte[]> fragments = outgo.getFragments();
        if (fragments == null || fragments.size() == 0) {
            return true;
        }
        int success = 0;
        Gate gate = getGate();
        for (byte[] pack : fragments) {
            if (gate.send(pack, remoteAddress)) {
                success += 1;
            }
        }
        long now = new Date().getTime();
        if (outgo.update(now)) {
            dock.appendDeparture(outgo);
        }
        return success == fragments.size();
    }

    @Override
    public boolean process() {
        // 1. check gate status
        if (!isConnected()) {
            // not connected yet
            return false;
        }
        // 2. get outgo
        Departure outgo = getOutgoShip();
        if (outgo == null) {
            // nothing to do now
            return false;
        }
        // 3. process outgo
        long now = (new Date()).getTime();
        if (outgo.isFailed(now)) {
            // outgo Ship expired, callback
            onError("Request timeout", outgo);
        } else if (!send(outgo)) {
            // failed to send outgo package, callback
            onError("Connection error", outgo);
        }
        return true;
    }

    @Override
    public void process(byte[] data) {
        // 1. get income ship from data package
        Arrival income = getIncomeShip(data);
        if (income == null) {
            // incomplete data package?
            return;
        } else {
            // remove linked ship (same SN, same page index)
            removeLinkedShip(income);
        }
        // 2. assemble package if incoming package is a fragment
        income = dock.assembleArrival(income);
        if (income == null) {
            // it's a fragment
            return;
        }
        // 3. callback
        Gate.Delegate delegate = getDelegate();
        assert delegate != null : "gate delegate should not empty";
        delegate.onReceived(income, remoteAddress, getGate());
    }

    /**
     *  Get income Ship from Connection
     */
    protected abstract Arrival getIncomeShip(byte[] data);

    protected void removeLinkedShip(Arrival income) {
        Departure linked = dock.checkResponse(income);
        if (linked != null) {
            // callback for the linked outgo Ship and remove it
            Gate.Delegate delegate = getDelegate();
            if (delegate != null) {
                delegate.onSent(linked, remoteAddress, getGate());
            }
        }
    }

    /**
     *  Get outgo Ship from waiting queue
     */
    protected Departure getOutgoShip() {
        return dock.getNextDeparture();
    }

    /**
     *  Get an empty ship
     */
    @Override
    public void heartbeat() {
        //send(pack(PING, Departure.Priority.SLOWER.value));
    }

    //
    //  Command bodies
    //
    protected static final byte[] PING = {'P', 'I', 'N', 'G'};
    protected static final byte[] PONG = {'P', 'O', 'N', 'G'};
    protected static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    protected static final byte[] OK = {'O', 'K'};
}
