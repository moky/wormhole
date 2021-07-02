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
package chat.dim.udp;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.List;

import chat.dim.mtp.ArrivalHall;
import chat.dim.mtp.DataType;
import chat.dim.mtp.Departure;
import chat.dim.mtp.DepartureHall;
import chat.dim.mtp.Package;
import chat.dim.mtp.TransactionID;
import chat.dim.net.ActiveConnection;
import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class ActivePackageHub extends BaseHub {

    private final ArrivalHall arrivalHall = new ArrivalHall();
    private final DepartureHall departureHall = new DepartureHall();

    private WeakReference<Connection.Delegate> delegateRef = null;

    public ActivePackageHub(Connection.Delegate delegate) {
        super();
        setDelegate(delegate);
    }

    public void setDelegate(Connection.Delegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }
    public Connection.Delegate getDelegate() {
        return delegateRef == null ? null : delegateRef.get();
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        ActiveConnection connection = new ActiveConnection(remote) {
            @Override
            protected Channel connect(SocketAddress remote) throws IOException {
                Channel channel = new DiscreteChannel();
                channel.configureBlocking(true);
                channel.connect(remote);
                channel.configureBlocking(false);
                if (local != null) {
                    channel.bind(local);
                }
                return channel;
            }
        };
        // set delegate
        Connection.Delegate delegate = getDelegate();
        if (delegate != null) {
            connection.setDelegate(delegate);
        }
        // start FSM
        connection.start();
        return connection;
    }

    @Override
    public byte[] receive(SocketAddress source, SocketAddress destination) {
        byte[] data;
        // 1. receive data
        do {
            data = super.receive(source, destination);
            if (data == null || data.length == 0) {
                // receive nothing
                break;
            }
            try {
                // process Command & Response
                data = processIncome(data, source, destination);
            } catch (IOException e) {
                e.printStackTrace();
                data = null;
            }
            // if data is null after processed, means it's a command or response
            // continue to receive another package
        } while (data == null);
        // 2. process waiting tasks
        try {
            processExpiredTasks();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return data;
    }

    @Override
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

    private void sendPackage(Package pack, SocketAddress source, SocketAddress destination) {
        byte[] data = pack.getBytes();
        assert data.length > 0 : "package size error";
        super.send(data, source, destination);
    }
    private void respond(DataType type, TransactionID sn, byte[] body,
                         SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(type, sn, new Data(body));
        sendPackage(pack, destination, source);
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

    //
    //  Arrival
    //

    private byte[] processIncome(byte[] data, SocketAddress source, SocketAddress destination) throws IOException {
        // create MTP package
        Package pack = Package.parse(new Data(data));
        if (pack == null) {
            return null;
        }
        DataType type = pack.head.type;
        ByteArray body = pack.body;
        if (body == null || body.getSize() == 0) {
            // should not happen
            return null;
        }
        if (type.isCommandResponse()) {
            // process CommandResponse:
            //      'PONG'
            //      'OK'
            return null;
        } else if (type.isCommand()) {
            // process Command:
            //      'PING'
            //      'NOOP'
            if (body.equals(PING)) {
                // PING -> PONG
                respond(DataType.CommandResponse, pack.head.sn, PONG, source, destination);
            } else if (body.equals(NOOP)) {
                // NOOP -> OK
                respond(DataType.CommandResponse, pack.head.sn, OK, source, destination);
            }
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
            departureHall.deleteFragment(pack.head.sn, pack.head.offset);
        } else if (type.isMessageFragment()) {
            // process MessageFragment:
            //      'OK'
            //      'AGAIN'
            respond(DataType.MessageResponse, pack.head.sn, OK, source, destination);
            // check cached fragments
            pack = arrivalHall.insertFragment(pack, source, destination);
            if (pack == null) {
                // not completed yet
                return null;
            }
            body = pack.body;
            if (body == null || body.getSize() == 0) {
                // should not happen
                return null;
            }
        } else {
            // process Message:
            //      'OK'
            //      'AGAIN'
            respond(DataType.MessageResponse, pack.head.sn, OK, source, destination);
        }
        // check body which should be in a Command
        if (body.equals(PING)) {
            respond(DataType.MessageResponse, pack.head.sn, PONG, source, destination);
            return null;
        } else if (body.equals(PONG)) {
            return null;
        } else if (body.equals(NOOP)) {
            return null;
        } else if (body.equals(OK)) {
            return null;
        } else if (body.equals(AGAIN)) {
            // TODO: reset maxRetries?
            return null;
        }
        return body.getBytes();
    }

    //
    //  Departure
    //

    private boolean sendDeparture(Departure task) {
        // get fragments
        List<Package> fragments = task.getFragments();
        if (fragments == null || fragments.size() == 0) {
            // all fragments respond?
            return false;
        }
        // send out all fragments
        for (Package pack : fragments) {
            sendPackage(pack, task.source, task.destination);
        }
        return true;
    }

    private static final byte[] PING = {'P', 'I', 'N', 'G'};
    private static final byte[] PONG = {'P', 'O', 'N', 'G'};
    private static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    private static final byte[] OK = {'O', 'K'};
    private static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
