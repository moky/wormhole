/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
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
import java.util.*;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.mtp.protocol.DataType;
import chat.dim.mtp.protocol.Header;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;
import chat.dim.mtp.task.Arrival;
import chat.dim.mtp.task.Assemble;
import chat.dim.mtp.task.Departure;
import chat.dim.tlv.Data;

public class MemPool implements Pool {

    /**
     *  1. Departure task should be expired after 2 minutes when receive no response.
     *  2. Assembling task should be expired after 2 minutes when receive nothing.
     */
    public static long EXPIRES = 120; // milliseconds

    // waiting list for responding
    private final List<Departure> departures = new ArrayList<>();
    private final ReadWriteLock departureLock = new ReentrantReadWriteLock();

    // waiting list for processing
    private final List<Arrival> arrivals = new ArrayList<>();
    private final ReadWriteLock arrivalLock = new ReentrantReadWriteLock();

    // waiting list for assembling
    private final Map<TransactionID, Assemble> assembles = new HashMap<>();
    private final ReadWriteLock assembleLock = new ReentrantReadWriteLock();

    public MemPool() {
        super();
    }

    private boolean isExpired(Departure task) {
        float now = (new Date()).getTime() / 1000.0f;
        return (task.getLastTime() + EXPIRES) < now;
    }

    private boolean isExpired(Assemble task) {
        float now = (new Date()).getTime() / 1000.0f;
        return (task.getLastTime() + EXPIRES) < now;
    }

    //
    //  Departures
    //

    @Override
    public Departure shiftExpiredDeparture() {
        Departure task = null;
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            if (departures.size() > 0) {
                if (isExpired(departures.get(0))) {
                    task = departures.remove(0);
                }
            }
        } finally {
            writeLock.unlock();
        }
        return task;
    }

    @Override
    public boolean appendDeparture(Departure task) {
        if (task.maxRetries < 0) {
            // too many retries
            return false;
        } else {
            task.maxRetries -= 1;
            task.updateLastTime();
        }
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            departures.add(task);
        } finally {
            writeLock.unlock();
        }
        return true;
    }

    @Override
    public boolean deleteDeparture(Package response, SocketAddress destination, SocketAddress source) {
        Header head = response.head;
        Data body = response.body;
        int bodyLen = body.length;
        TransactionID sn = head.sn;
        DataType type = head.type;
        if (type.equals(DataType.CommandRespond)) {
            // response for Command
            assert bodyLen == 0 || (body.getByte(0) == 'O' && body.getByte(1) == 'K') : "CommandRespond error: " + body;
            return deleteEntireTask(sn, destination);
        } else if (type.equals(DataType.MessageRespond)) {
            // response for Message or Fragment
            if (bodyLen >= 8) {
                // MessageFragment
                assert bodyLen == 8 || (body.getByte(8) == 'O' && body.getByte(9) == 'K') : "MessageRespond error: " + body;
                // get pages count and index
                int pages = (int) body.getUInt32Value(0);
                int offset = (int) body.getUInt32Value(4);
                assert pages > 1 && pages > offset : "pages error: " + pages + ", " + offset;
                return deleteFragment(sn, offset, destination);
            } else if (bodyLen == 0 || (body.getByte(0) == 'O' && body.getByte(1) == 'K')) {
                // Message
                return deleteEntireTask(sn, destination);
            } else {
                // respond for split message
                // TODO: if (body.equals("AGAIN")), resend all fragments of this message
                return false;
            }
        } else {
            throw new IllegalArgumentException("response type error: " + type);
        }
    }

    private boolean deleteEntireTask(TransactionID sn, SocketAddress destination) {
        int count = 0;
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            Departure task;
            int index = departures.size() - 1;
            for (; index >= 0; --index) {
                task = departures.get(index);
                if (!sn.equals(task.sn)) {
                    // transaction ID not match
                    continue;
                } else if (!destination.equals(task.destination)) {
                    // remote address not mach
                    continue;
                }
                // got it!
                departures.remove(index);
                count += 1;
                // break;
            }
        } finally {
            writeLock.unlock();
        }
        return count > 0;
    }

    private boolean deleteFragment(TransactionID sn, int offset, SocketAddress destination) {
        int count = 0;
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            List<Package> packages;
            Package pack;
            int pos;
            Departure task;
            int index = departures.size() - 1;
            for (; index >= 0; --index) {
                task = departures.get(index);
                if (!sn.equals(task.sn)) {
                    // transaction ID not match
                    continue;
                } else if (!destination.equals(task.destination)) {
                    // remote address not mach
                    continue;
                }
                // got it!
                packages = task.packages;
                pos = packages.size() - 1;
                for (; pos >= 0; --pos) {
                    pack = packages.get(pos);
                    assert sn.equals(pack.head.sn) : "trans ID error: " + pack;
                    assert DataType.MessageFragment.equals(pack.head.type) : "data type error: " + pack;
                    if (pack.head.offset == offset) {
                        // got it!
                        packages.remove(pos);
                        // break;
                    }
                }
                if (packages.size() == 0) {
                    // all fragments sent, remove this task
                    departures.remove(index);
                    count += 1;
                } else {
                    // update receive time
                    task.updateLastTime();
                }
            }
        } finally {
            writeLock.unlock();
        }
        return count > 0;
    }

    //
    //  Arrivals
    //

    @Override
    public int getCountOfArrivals() {
        int count;
        Lock readLock = arrivalLock.readLock();
        readLock.lock();
        try {
            count = arrivals.size();
        } finally {
            readLock.unlock();
        }
        return count;
    }

    @Override
    public Arrival shiftFirstArrival() {
        Arrival first = null;
        Lock writeLock = arrivalLock.writeLock();
        writeLock.lock();
        try {
            if (arrivals.size() > 0) {
                first = arrivals.remove(0);
            }
        } finally {
            writeLock.unlock();
        }
        return first;
    }

    @Override
    public boolean appendArrival(Arrival task) {
        Lock writeLock = arrivalLock.writeLock();
        writeLock.lock();
        try {
            arrivals.add(task);
        } finally {
            writeLock.unlock();
        }
        return true;
    }

    //
    //  Fragments Assembling
    //

    @Override
    public Package insertFragment(Package fragment, SocketAddress source, SocketAddress destination) {
        Package msg = null;
        Lock writeLock = assembleLock.writeLock();
        writeLock.lock();
        try {
            TransactionID sn = fragment.head.sn;
            Assemble task = assembles.get(sn);
            if (task == null) {
                // TODO: check incomplete message (fragment missed) from this source address
                //       if too many waiting fragments, deny receiving new message here

                // create new assemble
                task = new Assemble(fragment, source, destination);
                assembles.put(sn, task);
            } else {
                // insert fragment and check whether completed
                if (task.insert(fragment, source, destination)) {
                    if (task.isCompleted()) {
                        msg = Package.join(task.fragments);
                        assembles.remove(sn);
                    }
                }
            }
        } finally {
            writeLock.unlock();
        }
        return msg;
    }

    /**
     *  Remove all expired fragments
     *
     * @return assembling tasks
     */
    @Override
    public List<Assemble> discardFragments() {
        List<Assemble> tasks = new ArrayList<>();
        Lock writeLock = assembleLock.writeLock();
        writeLock.lock();
        try {
            // TransactionID key;
            Assemble value;
            Iterator<Map.Entry<TransactionID, Assemble>> iterator;
            Map.Entry<TransactionID, Assemble> item;
            for (iterator = assembles.entrySet().iterator(); iterator.hasNext();) {
                item = iterator.next();
                // key = item.getKey();
                value = item.getValue();
                if (isExpired(value)) {
                    // remove expired fragments
                    tasks.add(value);
                    iterator.remove();
                }
            }
        } finally {
            writeLock.unlock();
        }
        return tasks;
    }
}
