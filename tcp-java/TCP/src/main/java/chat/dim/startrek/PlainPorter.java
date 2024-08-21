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

import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import chat.dim.port.Arrival;
import chat.dim.port.Departure;

public class PlainPorter extends StarPorter {

    public PlainPorter(SocketAddress remote, SocketAddress local) {
        super(remote, local);
    }

    protected Arrival createArrival(byte[] pack) {
        return new PlainArrival(pack);
    }

    protected Departure createDeparture(byte[] pack, int priority) {
        return new PlainDeparture(pack, priority);
    }

    @Override
    protected List<Arrival> getArrivals(byte[] data) {
        if (data == null) {
            assert false : "should not happen";
            return null;
        }
        List<Arrival> ships = new ArrayList<>();
        ships.add(createArrival(data));
        return ships;
    }

    @Override
    protected Arrival checkArrival(Arrival income) {
        assert income instanceof PlainArrival : "arrival ship error: " + income;
        byte[] data = ((PlainArrival) income).getPackage();
        if (data.length == 4) {
            if (Arrays.equals(data, PING)) {
                // PING -> PONG
                send(PONG, Departure.Priority.SLOWER.value);
                return null;
            } else if (Arrays.equals(data, PONG)
                    || Arrays.equals(data, NOOP)) {
                // ignore
                return null;
            }
        }
        return income;
    }

    //
    //  Sending
    //

    public boolean send(byte[] payload, int priority) {
        // sending payload with priority
        return sendShip(createDeparture(payload, priority));
    }

    @Override
    public boolean sendData(byte[] payload) {
        return send(payload, Departure.Priority.NORMAL.value);
    }

    @Override
    public void heartbeat() {
        send(PING, Departure.Priority.SLOWER.value);
    }

    static final byte[] PING = {'P', 'I', 'N', 'G'};
    static final byte[] PONG = {'P', 'O', 'N', 'G'};
    static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    //static final byte[] OK = {'O', 'K'};

}
