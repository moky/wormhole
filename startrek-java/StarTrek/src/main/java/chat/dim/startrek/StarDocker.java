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

import java.io.IOException;
import java.net.SocketAddress;
import java.util.Date;
import java.util.List;

import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.port.Gate;

public abstract class StarDocker implements Docker {

    private final SocketAddress remoteAddress;
    private final SocketAddress localAddress;

    protected final Dock dock;

    protected StarDocker(SocketAddress remote, SocketAddress local) {
        super();
        remoteAddress = remote;
        localAddress = local;
        dock = createDock();
    }

    @Override
    public SocketAddress getRemoteAddress() {
        return remoteAddress;
    }

    @Override
    public SocketAddress getLocalAddress() {
        return localAddress;
    }

    // override for user-customized dock
    protected Dock createDock() {
        return new LockedDock();
    }

    protected abstract Gate getGate();

    protected abstract Gate.Delegate getDelegate();

    private boolean isReady() {
        Gate.Status status = getGate().getStatus(remoteAddress, localAddress);
        return status.equals(Gate.Status.READY);
    }

    @Override
    public boolean process() {
        // 1. check gate status
        if (!isReady()) {
            // not ready yet
            return false;
        }
        long now = (new Date()).getTime();
        // 2. get outgo
        Departure outgo = getOutgoShip(now);
        if (outgo == null) {
            // nothing to do now
            return false;
        }
        // 3. process outgo
        if (outgo.isFailed(now)) {
            // outgo Ship expired, callback
            onOutgoError("Request timeout", outgo);
        } else {
            try {
                if (!sendOutgoShip(outgo)) {
                    // failed to send outgo package, callback
                    onOutgoError("Connection error", outgo);
                }
            } catch (IOException e) {
                //e.printStackTrace();
                onOutgoError(e.getMessage(), outgo);
            }
        }
        return true;
    }
    private void onOutgoError(final String message, final Departure ship) {
        Gate.Delegate delegate = getDelegate();
        if (delegate != null) {
            delegate.onError(new Error(message), ship, localAddress, remoteAddress, getGate());
        }
    }

    @Override
    public void onReceived(final byte[] data) {
        // 1. get income ship from received data
        Arrival income = getIncomeShip(data);
        if (income == null) {
            return;
        }
        // 2. check income ship for response
        income = checkIncomeShip(income);
        if (income == null) {
            return;
        }
        // 3. process income ship with completed data package
        processIncomeShip(income);
    }

    /**
     *  Get income Ship from received data
     *
     * @param data - received data
     * @return income ship carrying data package/fragment
     */
    protected abstract Arrival getIncomeShip(final byte[] data);

    /**
     *  Check income ship for responding
     *
     * @param income - income ship carrying data package/fragment/response
     * @return income ship carrying completed data package
     */
    protected abstract Arrival checkIncomeShip(final Arrival income);

    /**
     *  Check and remove linked departure ship
     *
     * @param income - income ship with SN
     */
    protected void checkResponse(final Arrival income) {
        // check response for linked departure ship (same SN)
        Departure linked = dock.checkResponse(income);
        if (linked != null) {
            // all fragments responded, task finished
            Gate.Delegate delegate = getDelegate();
            if (delegate != null) {
                delegate.onSent(linked, localAddress, remoteAddress, getGate());
            }
        }
    }

    /**
     *  Process income ship
     *
     * @param income - income ship carrying completed data package
     */
    protected void processIncomeShip(final Arrival income) {
        Gate.Delegate delegate = getDelegate();
        assert delegate != null : "gate delegate should not empty";
        delegate.onReceived(income, remoteAddress, localAddress, getGate());
    }

    /**
     *  Get outgo Ship from waiting queue
     *
     * @param now - current time
     * @return next new or timeout task
     */
    protected Departure getOutgoShip(final long now) {
        // this will be remove from the queue,
        // if needs retry, the caller should append it back
        return dock.getNextDeparture(now);
    }

    /**
     *  Sending all fragments in the ship
     *
     * @param outgo - outgo ship carried package/fragments
     * @return true on sent
     */
    protected boolean sendOutgoShip(final Departure outgo) throws IOException {
        List<byte[]> fragments = outgo.getFragments();
        if (fragments == null || fragments.size() == 0) {
            return true;
        }
        int success = 0;
        Gate gate = getGate();
        for (byte[] pack : fragments) {
            if (gate.send(pack, localAddress, remoteAddress)) {
                success += 1;
            }
        }
        return success == fragments.size();
    }
}
