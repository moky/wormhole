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
package chat.dim.mtp;

import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

/**
 *  Memory cache for Departures
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public class DepartureHall {

    private final List<Departure> departures = new ArrayList<>();
    private final Map<TransactionID, Departure> departureMap = new WeakHashMap<>();

    private final Map<byte[], Long> departureFinished = new HashMap<>();  // ID -> timestamp
    private final ReadWriteLock departureLock = new ReentrantReadWriteLock();

    public void appendDeparture(Package pack, SocketAddress source, SocketAddress destination) {
        List<Package> fragments = Packer.split(pack);
        Departure task = new Departure(fragments, source, destination);
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            departures.add(task);
            departureMap.put(task.sn, task);
        } finally {
            writeLock.unlock();
        }
    }

    public void deleteFragment(TransactionID sn, int offset) {
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            byte[] snb = sn.getBytes();
            // check whether this task has already finished
            Long time = departureFinished.get(snb);
            if (time == null || time == 0) {
                // check departure
                Departure task = departureMap.get(sn);
                if (task != null && task.deleteFragment(offset)) {
                    // all fragments sent, remove this task
                    departures.remove(task);
                    departureMap.remove(sn);
                    // mark finished time
                    departureFinished.put(snb, (new Date()).getTime());
                }
            }
        } finally {
            writeLock.unlock();
        }
    }

    public void removeDeparture(Departure task) {
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            departures.remove(task);
            departureMap.remove(task.sn);
            departureFinished.put(task.sn.getBytes(), (new Date()).getTime());
        } finally {
            writeLock.unlock();
        }
    }

    public Departure getNextExpiredDeparture() {
        Departure expired = null;
        long now = (new Date()).getTime();
        Lock writeLock = departureLock.writeLock();
        writeLock.lock();
        try {
            for (Departure task : departures) {
                if (task.isExpired(now)) {
                    // got it
                    expired = task;
                    break;
                }
            }
        } finally {
            writeLock.unlock();
        }
        return expired;
    }
}
