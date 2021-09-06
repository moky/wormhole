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

import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.Arrays;
import java.util.List;

import chat.dim.port.Departure;
import chat.dim.port.Gate;

public class PlainDocker extends StarDocker<PlainDeparture, PlainArrival, Object> {

    private List<byte[]> advanceParties;

    private final WeakReference<StarGate<PlainDeparture, PlainArrival, Object>> gateRef;

    public PlainDocker(SocketAddress remote, SocketAddress local, List<byte[]> parties,
                       StarGate<PlainDeparture, PlainArrival, Object> gate) {
        super(remote, local);
        advanceParties = parties;
        gateRef = new WeakReference<>(gate);
    }

    @Override
    protected Gate getGate() {
        return gateRef.get();
    }

    @Override
    protected Gate.Delegate<PlainDeparture, PlainArrival, Object> getDelegate() {
        StarGate<PlainDeparture, PlainArrival, Object> gate = gateRef.get();
        return gate == null ? null : gate.getDelegate();
    }

    @Override
    public void process(byte[] data) {
        if (data != null) {
            super.process(data);
        } else if (advanceParties != null) {
            // process advance parties
            for (byte[] item : advanceParties) {
                super.process(item);
            }
            advanceParties = null;
        }
    }

    @Override
    protected PlainArrival getIncomeShip(byte[] data) {
        if (data == null || data.length == 0) {
            return null;
        }
        return new PlainArrival(data);
    }

    @Override
    protected PlainArrival checkIncomeShip(PlainArrival income) {
        byte[] data = income.getData();
        if (Arrays.equals(data, PING)) {
            // PING -> PONG
            PlainDeparture outgo = pack(PONG, Departure.Priority.SLOWER.value);
            dock.appendDeparture(outgo);
            return null;
        } else if (Arrays.equals(data, PONG)
                || Arrays.equals(data, NOOP)) {
            // ignore
            return null;
        }
        return income;
    }

    public void sendData(byte[] payload, int priority) {
        dock.appendDeparture(pack(payload, priority));
    }
    public void sendData(byte[] payload) {
        sendData(payload, Departure.Priority.NORMAL.value);
    }

    @Override
    public PlainDeparture pack(byte[] payload, int priority) {
        return new PlainDeparture(priority, payload);
    }

    @Override
    public void heartbeat() {
        PlainDeparture outgo = pack(PING, Departure.Priority.SLOWER.value);
        dock.appendDeparture(outgo);
    }

    static final byte[] PING = {'P', 'I', 'N', 'G'};
    static final byte[] PONG = {'P', 'O', 'N', 'G'};
    static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    //static final byte[] OK = {'O', 'K'};
}
