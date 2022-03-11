/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
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
package chat.dim.mtp;

import java.net.SocketAddress;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.startrek.DepartureShip;
import chat.dim.startrek.StarDocker;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class PackageDocker extends StarDocker {

    public PackageDocker(SocketAddress remote, SocketAddress local, Connection conn, Delegate delegate) {
        super(remote, local, conn, delegate);
    }

    protected Package parsePackage(byte[] data) {
        return data == null ? null : Package.parse(new Data(data));
    }

    protected Arrival createArrival(Package pkg) {
        return new PackageArrival(pkg);
    }

    protected Departure createDeparture(Package pkg, int priority) {
        return new PackageDeparture(pkg, priority);
    }

    @Override
    protected Departure getNextDeparture(long now) {
        Departure outgo = super.getNextDeparture(now);
        if (outgo != null) {
            retryDeparture(outgo);
        }
        return outgo;
    }

    protected void retryDeparture(Departure outgo) {
        if (outgo.getRetries() >= DepartureShip.MAX_RETRIES) {
            // last try
            return;
        }
        if (outgo instanceof PackageDeparture) {
            Package pack = ((PackageDeparture) outgo).getPackage();
            if (!pack.isResponse()) {
                // put back for next retry
                appendDeparture(outgo);
            }
        }
    }

    @Override
    protected Arrival getArrival(byte[] data) {
        Package pkg = parsePackage(data);
        if (pkg == null) {
            return null;
        }
        /* check body length?
        ByteArray body = pkg.body;
        if (body == null || body.getSize() == 0) {
            // should not happen
            return null;
        }
         */
        return createArrival(pkg);
    }

    @Override
    protected Arrival checkArrival(Arrival income) {
        assert income instanceof PackageArrival : "income ship error: " + income;
        PackageArrival ship = (PackageArrival) income;
        Package pkg = ship.getPackage();
        if (pkg == null) {
            List<Package> fragments = ship.getFragments();
            if (fragments == null || fragments.size() == 0) {
                throw new NullPointerException("fragments error: " + income);
            }
            // each ship can carry one fragment only
            pkg = fragments.get(0);
        }
        // check data type in package header
        Header head = pkg.head;
        DataType type = head.type;
        ByteArray body = pkg.body;

        if (type.isCommandResponse()) {
            // process CommandResponse:
            //      'PONG'
            //      'OK'
            checkResponse(income);
            if (body.equals(PONG) || body.equals(OK)) {
                // command responded
                return null;
            }
            // extra data in CommandResponse?
            // let the caller to process it
        } else if (type.isCommand()) {
            // process Command:
            //      'PING'
            //      '...'
            if (body.equals(PING)) {
                // PING -> PONG
                respondCommand(head.sn, PONG);
                return null;
            } else {
                // respond for Command
                respondCommand(head.sn, OK);
            }
            // Unknown Command?
            // let the caller to process it
        } else if (type.isMessageResponse()) {
            // process MessageResponse:
            //      'OK'
            //      'AGAIN'
            if (body.equals(AGAIN)) {
                // TODO: reset retries?
                return null;
            }
            checkResponse(income);
            if (body.equals(OK)) {
                // message responded
                return null;
            }
            // extra data in MessageResponse?
            // let the caller to process it
        } else {
            // respond for Message/Fragment
            respondMessage(head.sn, head.pages, head.index);
            if (type.isMessageFragment()) {
                // assemble MessageFragment with cached fragments to completed Message
                // let the caller to process the completed message
                return assembleArrival(income);
            }
            assert type.isMessage() : "unknown data type: " + type;
            // let the caller to process the message
        }

        if (body.getSize() == 4) {
            if (body.equals(NOOP)) {
                // do nothing
                return null;
            } else if (body.equals(PING) || body.equals(PONG)) {
                // FIXME: these bodies should be in a Command
                // ignore them
                return null;
            }
        }

        return income;
    }

    //
    //  Sending
    //

    protected void respondCommand(TransactionID sn, byte[] body) {
        send(Package.create(DataType.COMMAND_RESPONSE, sn, 1, 0, -1, new Data(body)));
    }
    protected void respondMessage(TransactionID sn, int pages, int index) {
        send(Package.create(DataType.MESSAGE_RESPONSE, sn, pages, index, -1, new Data(OK)));
    }

    public boolean send(Package pkg) {
        return send(pkg, Departure.Priority.NORMAL.value);
    }

    public boolean send(Package pkg, int priority) {
        return send(createDeparture(pkg, priority));
    }
    public boolean send(Departure ship) {
        return appendDeparture(ship);
    }

    @Override
    public Departure pack(byte[] payload, int priority) {
        Package pkg = Package.create(DataType.MESSAGE, null, 1, 0, -1, new Data(payload));
        return createDeparture(pkg, priority);
    }

    @Override
    public void heartbeat() {
        Package pkg = Package.create(DataType.COMMAND, null, 1, 0, -1, new Data(PING));
        send(createDeparture(pkg, Departure.Priority.SLOWER.value));
    }

    protected static final byte[] PING = {'P', 'I', 'N', 'G'};
    protected static final byte[] PONG = {'P', 'O', 'N', 'G'};
    protected static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    protected static final byte[] OK = {'O', 'K'};
    protected static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
