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

import java.util.List;

import chat.dim.net.Connection;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.startrek.StarDocker;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class PackageDocker extends StarDocker {

    public PackageDocker(Connection conn) {
        super(conn);
    }

    protected Package parsePackage(byte[] data) {
        return data == null ? null : Package.parse(new Data(data));
    }

    protected Arrival createArrival(Package pkg) {
        return new PackageArrival(pkg);
    }

    protected Departure createDeparture(Package pkg, int priority) {
        if (pkg.isMessage()) {
            // normal package
            return new PackageDeparture(pkg, priority);
        } else {
            // command package needs no response, and
            // response package needs no response again,
            // so this ship will be removed immediately after sent.
            return new PackageDeparture(pkg, priority, 1);
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

    protected Package createCommand(byte[] body) {
        return Package.create(DataType.COMMAND, null, 1, 0, -1, new Data(body));
    }
    protected Package createMessage(byte[] body) {
        return Package.create(DataType.MESSAGE, null, 1, 0, -1, new Data(body));
    }
    protected Package createCommandResponse(TransactionID sn, byte[] body) {
        return Package.create(DataType.COMMAND_RESPONSE, sn, 1, 0, -1, new Data(body));
    }
    protected Package createMessageResponse(TransactionID sn, int pages, int index) {
        return Package.create(DataType.MESSAGE_RESPONSE, sn, pages, index, -1, new Data(OK));
    }

    protected void respondCommand(TransactionID sn, byte[] body) {
        sendPackage(createCommandResponse(sn, body));
    }
    protected void respondMessage(TransactionID sn, int pages, int index) {
        sendPackage(createMessageResponse(sn, pages, index));
    }

    public boolean sendCommand(byte[] body) {
        return sendPackage(createCommand(body), Departure.Priority.SLOWER.value);
    }
    public boolean sendMessage(byte[] body) {
        return sendPackage(createMessage(body), Departure.Priority.NORMAL.value);
    }

    public boolean sendPackage(Package pkg) {
        return sendPackage(pkg, Departure.Priority.NORMAL.value);
    }

    public boolean sendPackage(Package pkg, int priority) {
        // send data package with priority
        return sendShip(createDeparture(pkg, priority));
    }

    @Override
    public boolean sendData(byte[] payload) {
        return sendMessage(payload);
    }

    @Override
    public void heartbeat() {
        boolean ok = sendCommand(PING);
        assert ok : "failed to send command: PING";
    }

    protected static final byte[] PING = {'P', 'I', 'N', 'G'};
    protected static final byte[] PONG = {'P', 'O', 'N', 'G'};
    protected static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    protected static final byte[] OK = {'O', 'K'};
    protected static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
