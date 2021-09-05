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

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.List;

import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.startrek.StarDocker;
import chat.dim.startrek.StarGate;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class PackageDocker extends StarDocker {

    private ByteArray cached = null;

    private final WeakReference<StarGate> gateRef;

    public PackageDocker(SocketAddress remote, byte[] advanceParty, StarGate gate) {
        super(remote);
        if (advanceParty != null && advanceParty.length > 0) {
            cached = new Data(advanceParty);
        }
        gateRef = new WeakReference<>(gate);
    }

    @Override
    protected Gate getGate() {
        return gateRef.get();
    }

    @Override
    protected Gate.Delegate getDelegate() {
        StarGate gate = gateRef.get();
        return gate == null ? null : gate.getDelegate();
    }

    @Override
    public void process(final byte[] data) {
        if (data != null) {
            if (cached == null) {
                cached = new Data(data);
            } else {
                cached = cached.concat(data);
            }
        }
        if (cached != null && cached.getSize() > 0) {
            super.process(cached.getBytes());
        }
    }

    private Package getPackage(ByteArray data) {
        Header head = Header.parse(data);
        if (head == null) {
            // FIXME: data error?
            cached = null;
            return null;
        }
        int dataLen = data.getSize();
        int headLen = head.getSize();
        int bodyLen = head.bodyLength;
        int packLen = bodyLen == -1 ? dataLen : headLen + bodyLen;
        if (/*bodyLen == -1 || */packLen == dataLen) {
            // no sticky data after the tail
            cached = null;
        } else if (packLen < dataLen) {
            // cut the tail
            cached = data.slice(packLen);
            data = data.slice(0, packLen);
        } else {
            // wait for more data
            return null;
        }
        return new Package(data, head, data.slice(head.getSize()));
    }

    @Override
    protected Arrival getIncomeShip(byte[] data) {
        Package pack = getPackage(new Data(data));
        if (pack == null) {
            return null;
        }
        ByteArray body = pack.body;
        if (body == null || body.getSize() == 0) {
            // should not happen
            return null;
        }
        return new PackageArrival(pack);
    }

    @Override
    protected Arrival checkIncomeShip(Arrival income) {
        assert income instanceof PackageArrival : "income ship error: " + income;
        Package pack = ((PackageArrival) income).getPackage();
        if (pack == null) {
            List<Package> fragments = ((PackageArrival) income).getFragments();
            if (fragments == null || fragments.size() == 0) {
                throw new NullPointerException("fragments error: " + income);
            }
            // each ship can carry one fragment only
            pack = fragments.get(0);
        }
        // check data type in package header
        Header head = pack.head;
        DataType type = head.type;
        ByteArray body = pack.body;

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
            }
            // respond for Command
            respondCommand(head.sn, OK);
            // Unknown Command?
            // let the caller to process it
        } else if (type.isMessageResponse()) {
            // process MessageResponse:
            //      'OK'
            //      'AGAIN'
            if (body.equals(AGAIN)) {
                // TODO: reset maxRetries?
                return null;
            }
            checkResponse(income);
            if (body.equals(OK)) {
                // message responded
                return null;
            }
            // extra data in MessageResponse?
            // let the caller to process it
        } else if (type.isMessageFragment()) {
            // assemble MessageFragment with cached fragments to completed Message
            income = dock.assembleArrival(income);
            // let the caller to process the completed message
        } else if (type.isMessage()) {
            // respond for Message
            respondMessage(head.sn, head.pages, head.index);
            // let the caller to process the message
        }

        if (body.equals(NOOP)) {
            // do nothing
            return null;
        } else if (body.equals(PING) || body.equals(PONG)) {
            // FIXME: these bodies should be in a Command
            // ignore them
            return null;
        }

        return income;
    }

    @Override
    protected boolean sendOutgoShip(final Departure outgo) throws IOException {
        List<byte[]> fragments = outgo.getFragments();
        if (fragments == null || fragments.size() == 0) {
            return true;
        }
        if (outgo.getRetries() < 2) {
            // FIXME:
            dock.appendDeparture(outgo);
        }
        int success = 0;
        Gate gate = getGate();
        for (byte[] pack : fragments) {
            if (gate.send(pack, remoteAddress)) {
                success += 1;
            }
        }
        return success == fragments.size();
    }

    private void respondCommand(TransactionID sn, byte[] body) {
        Package pack = Package.create(DataType.COMMAND_RESPONSE, sn, new Data(body));
        sendPackage(pack);
    }
    private void respondMessage(TransactionID sn, int pages, int index) {
        Package pack = Package.create(DataType.MESSAGE_RESPONSE, sn, pages, index, new Data(OK));
        sendPackage(pack);
    }

    public void sendPackage(Package pack, int priority) {
        Departure ship = new PackageDeparture(priority, pack);
        dock.appendDeparture(ship);
    }
    public void sendPackage(Package pack) {
        sendPackage(pack, Departure.Priority.NORMAL.value);
    }

    @Override
    public Departure pack(byte[] payload, int priority) {
        Package pack = Package.create(DataType.MESSAGE, new Data(payload));
        return new PackageDeparture(priority, pack);
    }

    @Override
    public void heartbeat() {
        Package pack = Package.create(DataType.COMMAND, new Data(PING));
        sendPackage(pack, Departure.Priority.SLOWER.value);
    }

    static final byte[] PING = {'P', 'I', 'N', 'G'};
    static final byte[] PONG = {'P', 'O', 'N', 'G'};
    static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    static final byte[] OK = {'O', 'K'};
    static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
