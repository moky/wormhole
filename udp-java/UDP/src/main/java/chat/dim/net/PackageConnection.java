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

    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        // create MTP package
        Package pack = Package.create(DataType.Message, new Data(data));
        // append as Departure task to waiting queue
        departureHall.appendDeparture(pack, source, destination);
        try {
            processExpiredTasks();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return 0;
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
            sendPackage(pack, task.destination);
        }
        return true;
    }

    private void sendPackage(Package pack, SocketAddress remote) {
        byte[] data = pack.getBytes();
        ByteBuffer buffer = ByteBuffer.allocate(data.length);
        buffer.put(data);
        buffer.flip();
        try {
            send(buffer, remote);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public byte[] receive(SocketAddress source, SocketAddress destination) throws IOException {
        ByteBuffer buffer = ByteBuffer.allocate(MSS);
        byte[] data;
        do {
            buffer.clear();
            SocketAddress remote = receive(buffer);
            if (remote == null) {
                return null;
            }
            assert source == null || source.equals(remote) : "source address error: " + source + ", " + remote;
            data = new byte[buffer.position()];
            buffer.flip();
            buffer.get(data);
            data = processIncome(data, remote, destination);
        } while (data == null);
        return data;
    }
    private byte[] processIncome(byte[] data, SocketAddress remote, SocketAddress destination) {
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
        if (type.isCommand()) {
            // process Command:
            //      'PING'
            //      'NOOP'
            if (body.equals(PING)) {
                // PING -> PONG
                respondCommand(head.sn, PONG, remote);
            } else if (body.equals(NOOP)) {
                // NOOP -> OK
                respondCommand(head.sn, OK, remote);
            }
            return null;
        } else if (type.isCommandResponse()) {
            // process CommandResponse:
            //      'PONG'
            //      'OK'
            return null;
        } else if (type.isMessageResponse()) {
            // process MessageResponse:
            //      'OK'
            //      'AGAIN'
            //      'PONG'
            if (body.equals(AGAIN)) {
                // TODO: reset maxRetries?
                return null;
            }
            departureHall.deleteFragment(head.sn, head.offset);
        } else if (type.isMessageFragment()) {
            // process MessageFragment:
            //      'OK'
            //      'AGAIN'
            Package res = Package.create(DataType.MessageResponse, head.sn, head.pages, head.offset, new Data(OK));
            sendPackage(res, remote);
            // check cached fragments
            pack = arrivalHall.insertFragment(pack, remote, destination);
            if (pack == null) {
                // not completed yet
                return null;
            }
            body = pack.body;
            if (body == null || body.getSize() == 0) {
                // should not happen
                return null;
            }
        } else if (type.isMessage()) {
            // process Message:
            //      'OK'
            //      'AGAIN'
            Package res = Package.create(DataType.MessageResponse, head.sn, new Data(OK));
            sendPackage(res, remote);
        } else {
            // should not happen
            throw new IllegalArgumentException("data type error: " + type);
        }
        // check body which should be in a Command
        if (body.equals(PING) || body.equals(PONG) || body.equals(NOOP) || body.equals(OK)) {
            // ignore
            return null;
        } else {
            return body.getBytes();
        }
    }
    private void respondCommand(TransactionID sn, byte[] body, SocketAddress remote) {
        Package pack = Package.create(DataType.CommandResponse, sn, new Data(body));
        sendPackage(pack, remote);
    }

    public void heartbeat(SocketAddress remote) {
        Package pack = Package.create(DataType.Command, new Data(PING));
        sendPackage(pack, remote);
    }

    private static final byte[] PING = {'P', 'I', 'N', 'G'};
    private static final byte[] PONG = {'P', 'O', 'N', 'G'};
    private static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    private static final byte[] OK = {'O', 'K'};
    private static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
