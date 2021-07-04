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

public abstract class PackageConnection extends ActiveConnection {

    /*  Maximum Segment Size
     *  ~~~~~~~~~~~~~~~~~~~~
     *  Buffer size for receiving package
     *
     *  MTU        : 1500 bytes (excludes 14 bytes ethernet header & 4 bytes FCS)
     *  IP header  :   20 bytes
     *  TCP header :   20 bytes
     *  UDP header :    8 bytes
     */
    public static int MSS = 1472;  // 1500 - 20 - 8

    private final ArrivalHall arrivalHall = new ArrivalHall();
    private final DepartureHall departureHall = new DepartureHall();

    public PackageConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super(byteChannel, remote, local);
    }

    public PackageConnection(SocketAddress remote, SocketAddress local) {
        super(remote, local);
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

    /**
     *  Append the package into a waiting queue for sending out
     *
     * @param pack        - data package
     * @param source      - local address
     * @param destination - remote address
     * @throws IOException on error
     */
    public void sendPackage(Package pack, SocketAddress source, SocketAddress destination) throws IOException {
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

    private boolean sendDeparture(Departure task) {
        // get fragments
        List<Package> fragments = task.getFragments();
        if (fragments == null || fragments.size() == 0) {
            // all fragments respond?
            return false;
        }
        // send out all fragments
        for (Package pack : fragments) {
            sendData(pack.getBytes(), task.destination);
        }
        return true;
    }

    private void sendData(byte[] data, SocketAddress remote) {
        ByteBuffer buffer = ByteBuffer.allocate(data.length);
        buffer.put(data);
        buffer.flip();
        try {
            send(buffer, remote);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    private void respondCommand(TransactionID sn, byte[] body, SocketAddress remote) {
        Package res = Package.create(DataType.CommandResponse, sn, new Data(body));
        sendData(res.getBytes(), remote);
    }
    private void respondMessage(TransactionID sn, int pages, int offset, SocketAddress remote) {
        Package res = Package.create(DataType.MessageResponse, sn, pages, offset, new Data(OK));
        sendData(res.getBytes(), remote);
    }

    /**
     *  Receive data package from remote address
     *
     * @param source      - remote address
     * @param destination - local address
     * @return complete package
     * @throws IOException on error
     */
    public Package receivePackage(SocketAddress source, SocketAddress destination) throws IOException {
        Package pack;
        ByteBuffer buffer = ByteBuffer.allocate(MSS);
        SocketAddress remote;
        byte[] data;
        while (true) {
            buffer.clear();
            remote = receive(buffer);
            if (remote == null) {
                // received nothing
                return null;
            }
            assert source == null || source.equals(remote) : "source address error: " + source + ", " + remote;
            data = new byte[buffer.position()];
            buffer.flip();
            buffer.get(data);
            pack = processIncome(data, remote, destination);
            if (pack != null) {
                // received a complete package
                return pack;
            }
        }
    }
    private Package processIncome(byte[] data, SocketAddress remote, SocketAddress destination) {
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
            assert head.offset == 0 : "command offset error: " + head.offset;
            departureHall.deleteFragment(head.sn, head.offset);
            if (body.equals(PONG)) {
                // ignore
                return null;
            } else if (body.equals(OK)) {
                // ignore
                return null;
            }
            // Unknown Command Response?
            // let the caller to process it
        } else if (type.isCommand()) {
            // process Command:
            //      'PING'
            //      'NOOP'
            if (body.equals(PING)) {
                // PING -> PONG
                respondCommand(head.sn, PONG, remote);
                return null;
            } else if (body.equals(NOOP)) {
                // NOOP -> OK
                respondCommand(head.sn, OK, remote);
                return null;
            }
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
            departureHall.deleteFragment(head.sn, head.offset);
            if (body.equals(OK)) {
                return null;
            } else if (body.equals(PONG)) {
                // this body should be in a Command
                return null;
            }
            // Unknown Message Response?
            // let the caller to process it
        } else if (type.isMessageFragment()) {
            // process MessageFragment:
            //      'OK'
            //      'AGAIN'
            respondMessage(head.sn, head.pages, head.offset, remote);
            // check cached fragments
            pack = arrivalHall.insertFragment(pack, remote, destination);
        } else {
            // process Message:
            //      '...'
            assert type.isMessage() : "data type error: " + type;
            if (body.equals(PING) || body.equals(PONG) || body.equals(NOOP) || body.equals(OK)) {
                // these bodies should be in a Command
                // ignore them
                return null;
            }
            respondMessage(head.sn, 1, 0, remote);
        }
        return pack;
    }

    /**
     *  Send a heartbeat package to remote address
     *
     * @param destination - remote address
     */
    public void heartbeat(SocketAddress destination) {
        Package pack = Package.create(DataType.Command, new Data(PING));
        sendData(pack.getBytes(), destination);
    }

    private static final byte[] PING = {'P', 'I', 'N', 'G'};
    private static final byte[] PONG = {'P', 'O', 'N', 'G'};
    private static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    private static final byte[] OK = {'O', 'K'};
    private static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
