/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.net;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.util.List;

import chat.dim.mtp.ArrivalHall;
import chat.dim.mtp.DataType;
import chat.dim.mtp.Departure;
import chat.dim.mtp.DepartureHall;
import chat.dim.mtp.Header;
import chat.dim.mtp.Package;
import chat.dim.mtp.TransactionID;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class PackageConnection extends BaseConnection {

    private final ArrivalHall arrivalHall = new ArrivalHall();
    private final DepartureHall departureHall = new DepartureHall();

    public PackageConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super(byteChannel, remote, local);
    }

    @Override
    public void tick() {
        super.tick();
        try {
            processExpiredTasks();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void process() throws IOException {
        Delegate delegate = getDelegate();
        if (delegate == null) {
            return;
        }
        // receiving
        ByteBuffer buffer = ByteBuffer.allocate(MSS);
        SocketAddress remote = receive(buffer);
        if (remote == null) {
            return;
        }
        byte[] data = new byte[buffer.position()];
        buffer.flip();
        buffer.get(data);
        // process for package
        Package pack = processIncome(data, remote, getLocalAddress());
        if (pack == null) {
            return;
        }
        // callback
        delegate.onConnectionDataReceived(this, remote, pack.head, pack.body.getBytes());
    }

    /**
     *  Append the package into a waiting queue for sending out
     *
     * @param body        - message body
     * @param source      - local address
     * @param destination - remote address
     * @throws IOException on error
     */
    public void sendCommand(byte[] body, SocketAddress source, SocketAddress destination) throws IOException {
        Package pack = Package.create(DataType.COMMAND, new Data(body));
        // append as Departure task to waiting queue
        departureHall.appendDeparture(pack, source, destination);
        // send out tasks from waiting queue
        processExpiredTasks();
    }
    public void sendMessage(byte[] body, SocketAddress source, SocketAddress destination) throws IOException {
        Package pack = Package.create(DataType.MESSAGE, new Data(body));
        // append as Departure task to waiting queue
        departureHall.appendDeparture(pack, source, destination);
        // send out tasks from waiting queue
        processExpiredTasks();
    }

    private void processExpiredTasks() throws IOException {
        // check departures
        Departure outgo;
        while (true) {
            outgo = departureHall.getNextExpiredDeparture();
            if (outgo == null) {
                // all job done
                break;
            } else if (!sendDeparture(outgo)) {
                // task error
                departureHall.removeDeparture(outgo);
            }
        }
        // check arrivals
        arrivalHall.clearExpiredArrivals();
    }

    private boolean sendDeparture(Departure task) throws IOException {
        // get fragments
        List<Package> fragments = task.getFragments();
        if (fragments == null || fragments.size() == 0) {
            // all fragments respond?
            return false;
        }
        // send out all fragments
        for (Package pack : fragments) {
            send(pack.getBytes(), task.destination);
        }
        return true;
    }

    private void respondCommand(TransactionID sn, byte[] body, SocketAddress remote) throws IOException {
        Package res = Package.create(DataType.COMMAND_RESPONSE, sn, new Data(body));
        send(res.getBytes(), remote);
    }
    private void respondMessage(TransactionID sn, int pages, int index, SocketAddress remote) throws IOException {
        Package res = Package.create(DataType.MESSAGE_RESPONSE, sn, pages, index, new Data(OK));
        send(res.getBytes(), remote);
    }

    private Package processIncome(byte[] data, SocketAddress remote, SocketAddress destination) throws IOException {
        // process income package
        Package pack = Package.parse(new Data(data));
        if (pack == null) {
            return null;
        }
        ByteArray body = pack.body;
        if (body == null || body.getSize() == 0) {
            // should not happen
            return null;
        }
        // check data type in package header
        Header head = pack.head;
        DataType type = head.type;

        if (type.isCommandResponse()) {
            // process CommandResponse:
            //      'PONG'
            //      'OK'
            assert head.index == 0 : "command index error: " + head.index;
            departureHall.deleteFragment(head.sn, head.index);
            if (body.equals(PONG) || body.equals(OK)) {
                // ignore
                return null;
            }
            // Unknown Command Response?
            // let the caller to process it
        } else if (type.isCommand()) {
            // process Command:
            //      'PING'
            //      '...'
            if (body.equals(PING)) {
                // PING -> PONG
                respondCommand(head.sn, PONG, remote);
                return null;
            }
            respondCommand(head.sn, OK, remote);
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
            departureHall.deleteFragment(head.sn, head.index);
            if (body.equals(OK)) {
                // ignore
                return null;
            }
            // Unknown Message Response?
            // let the caller to process it
        } else {
            // process Message/Fragment:
            //      '...'
            respondMessage(head.sn, head.pages, head.index, remote);
            if (type.isFragment()) {
                // check cached fragments
                pack = arrivalHall.insertFragment(pack, remote, destination);
            }
            // let the caller to process the message
        }

        if (body.equals(NOOP)) {
            // do nothing
            return null;
        }
        if (body.equals(PING) || body.equals(PONG)) {
            // FIXME: these bodies should be in a Command
            // ignore them
            return null;
        }
        return pack;
    }

    static final byte[] PING = {'P', 'I', 'N', 'G'};
    static final byte[] PONG = {'P', 'O', 'N', 'G'};
    static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    static final byte[] OK = {'O', 'K'};
    static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
