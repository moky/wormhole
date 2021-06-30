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
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.mtp.Arrival;
import chat.dim.mtp.DataType;
import chat.dim.mtp.Departure;
import chat.dim.mtp.Package;
import chat.dim.mtp.Packer;
import chat.dim.mtp.TransactionID;
import chat.dim.net.BaseConnection;
import chat.dim.net.Channel;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class PackageConnection extends BaseConnection {

    //
    //  Outgoing
    //
    private final Map<TransactionID, Departure> departures = new HashMap<>();
    private final List<TransactionID> departureQueue = new ArrayList<>();
    private final Map<byte[], Long> departureFinished = new HashMap<>();       // ID -> timestamp
    private final ReadWriteLock departureLock = new ReentrantReadWriteLock();

    //
    //  Incoming
    //
    private final Map<TransactionID, Arrival> arrivals = new HashMap<>();
    private final Map<byte[], Long> arrivalFinished = new HashMap<>();       // ID -> timestamp
    private final ReadWriteLock arrivalLock = new ReentrantReadWriteLock();

    public PackageConnection(Channel channel) {
        super(channel);
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        SocketAddress remote = super.receive(dst);
        if (remote != null) {
            // get data from buffer
            dst.flip();
            int len = dst.limit() - dst.position();
            assert len > 0 : "buffer error";
            byte[] data = new byte[len];
            dst.get(data);
            // process data
            try {
                data = processIncome(data, remote);
            } catch (IOException e) {
                e.printStackTrace();
                data = null;
            }
            // response
            if (data != null && data.length > 0) {
                dst.clear();
                len = dst.limit();
                if (len > data.length) {
                    len = data.length;
                }
                dst.put(data, 0, len);
            }
        }
        // process
        processExpiredTasks();
        return remote;
    }

    @Override
    public int send(ByteBuffer src, SocketAddress target) throws IOException {
        // get data from buffer
        int len = src.limit() - src.position();
        assert len > 0 : "buffer empty";
        byte[] data = new byte[len];
        src.get(data);
        // create MTP package
        Package pack = Package.create(DataType.Message, new Data(data));
        List<Package> fragments = Packer.split(pack);
        // append as Departure task to waiting queue
        appendDeparture(new Departure(fragments, target));
        // process
        processExpiredTasks();
        return 0;
    }

    private void sendPackage(Package pack, SocketAddress target) throws IOException {
        byte[] data = pack.getBytes();
        assert data.length > 0 : "package size error";
        ByteBuffer buffer = ByteBuffer.allocate(data.length);
        buffer.put(data);
        buffer.flip();
        super.send(buffer, target);
    }
    private void respond(DataType type, TransactionID sn, byte[] body, SocketAddress target) throws IOException {
        Package pack = Package.create(type, sn, new Data(body));
        sendPackage(pack, target);
    }

    private void processExpiredTasks() throws IOException {
        // check departures
        Departure outgo;
        while (true) {
            outgo = getNextExpiredDeparture();
            if (outgo == null) {
                // all job done
                break;
            } else if (!sendDeparture(outgo)) {
                // task error
                removeDeparture(outgo);
            }
        }
        // check arrivals
        Lock writeLock = arrivalLock.writeLock();
        writeLock.lock();
        try {
            long now = (new Date()).getTime();
            Arrival income;
            Set<TransactionID> keys = arrivals.keySet();
            for (TransactionID sn : keys) {
                income = arrivals.get(sn);
                if (income != null && income.isExpired(now)) {
                    arrivals.remove(sn);
                }
            }
        } finally {
            writeLock.unlock();
        }
    }

    //
    //  Arrival
    //

    private byte[] processIncome(byte[] data, SocketAddress source) throws IOException {
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
                respond(DataType.CommandResponse, pack.head.sn, PONG, source);
            } else if (body.equals(NOOP)) {
                // NOOP -> OK
                respond(DataType.CommandResponse, pack.head.sn, OK, source);
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
            deleteDeparture(pack);
        } else if (type.isMessageFragment()) {
            // process MessageFragment:
            //      'OK'
            //      'AGAIN'
            respond(DataType.MessageResponse, pack.head.sn, OK, source);
            // check cached fragments
            pack = insertFragment(pack);
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
            respond(DataType.MessageResponse, pack.head.sn, OK, source);
        }
        // check body which should be in a Command
        if (body.equals(PING)) {
            respond(DataType.MessageResponse, pack.head.sn, PONG, source);
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

    private Package insertFragment(Package fragment) {
        TransactionID sn = fragment.head.sn;
        byte[] snb = sn.getBytes();
        Package pack = null;
        Lock writeLock = arrivalLock.writeLock();
        writeLock.lock();
        try {
            // check whether the task has already finished
            Long time = arrivalFinished.get(snb);
            if (time == null || time == 0) {
                // check arrivals
                Arrival task = arrivals.get(sn);
                if (task == null) {
                    // new arrival
                    task = new Arrival(sn, fragment.head.pages);
                    arrivals.put(sn, task);
                }
                // insert
                pack = task.insert(fragment);
                if (pack != null) {
                    // completed!
                    arrivalFinished.put(snb, (new Date()).getTime());
                    arrivals.remove(sn);
                }
            }
        } finally {
            writeLock.unlock();
        }
        return pack;
    }

    //
    //  Departure
    //

    private void deleteDeparture(Package response) {
        TransactionID sn = response.head.sn;
        byte[] snb = sn.getBytes();
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            // check whether this task has already finished
            Long time = departureFinished.get(snb);
            if (time == null || time == 0) {
                // check departure
                Departure task = departures.get(sn);
                if (task == null || task.deleteFragment(response.head.offset)) {
                    // task finished
                    departures.remove(sn);
                    departureQueue.remove(sn);
                    departureFinished.put(snb, (new Date()).getTime());
                }
            }
        } finally {
            writeLock.unlock();
        }
    }

    private void removeDeparture(Departure task) {
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            departures.remove(task.sn);
            departureQueue.remove(task.sn);
            departureFinished.put(task.sn.getBytes(), (new Date()).getTime());
        } finally {
            writeLock.unlock();
        }
    }

    private boolean sendDeparture(Departure task) throws IOException {
        // 1. get fragments
        List<Package> fragments = task.getFragments();
        if (fragments == null || fragments.size() == 0) {
            // all fragments respond?
            return false;
        }
        // 2. get max size of buffer for every fragments
        int capacity = 0;
        for (Package pack : fragments) {
            if (pack.getSize() > capacity) {
                capacity = pack.getSize();
            }
        }
        if (capacity <= 0) {
            // should not happen
            return false;
        }
        // 3. send out all fragments
        for (Package pack : fragments) {
            sendPackage(pack, task.remote);
        }
        return true;
    }

    private Departure getNextExpiredDeparture() {
        Departure expired = null;
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            long now = (new Date()).getTime();
            Departure item;
            for (TransactionID sn : departureQueue) {
                item = departures.get(sn);
                if (item != null && item.isExpired(now)) {
                    // got it
                    expired = item;
                    break;
                }
            }
        } finally {
            writeLock.unlock();
        }
        return expired;
    }

    private void appendDeparture(Departure task) {
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            departures.put(task.sn, task);
            departureQueue.add(task.sn);
        } finally {
            writeLock.unlock();
        }
    }

    private static final byte[] PING = {'P', 'I', 'N', 'G'};
    private static final byte[] PONG = {'P', 'O', 'N', 'G'};
    private static final byte[] NOOP = {'N', 'O', 'O', 'P'};
    private static final byte[] OK = {'O', 'K'};
    private static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
