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
import java.util.Arrays;

import chat.dim.net.Connection;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;

public class PlainDocker extends StarDocker {

    public PlainDocker(Connection conn, Delegate delegate) {
        super(conn, delegate);
    }

    protected Arrival createArrival(byte[] data) {
        return new PlainArrival(data);
    }

    @Override
    protected Arrival getArrival(byte[] data) {
        if (data == null || data.length == 0) {
            return null;
        }
        return createArrival(data);
    }

    @Override
    protected Arrival checkArrival(Arrival income) {
        assert income instanceof PlainArrival : "arrival ship error: " + income;
        byte[] data = ((PlainArrival) income).getPackage();
        if (data.length == 4) {
            if (Arrays.equals(data, PING)) {
                // PING -> PONG
                appendDeparture(pack(PONG, Departure.Priority.SLOWER.value));
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

    public boolean send(byte[] payload) {
        return send(payload, Departure.Priority.NORMAL.value);
    }

    public boolean send(byte[] payload, int priority) {
        Departure ship = pack(payload, priority);
        return send(ship);
    }
    public boolean send(Departure ship) {
        return appendDeparture(ship);
    }

    @Override
    public PlainDeparture pack(byte[] payload, int priority) {
        return new PlainDeparture(payload, priority);
    }

    @Override
    public void heartbeat() {
        Departure ship = pack(PING, Departure.Priority.SLOWER.value);
        send(ship);
    }

    static final byte[] PING = {'P', 'I', 'N', 'G'};
    static final byte[] PONG = {'P', 'O', 'N', 'G'};
    static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    //static final byte[] OK = {'O', 'K'};
}
