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
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

/**
 *  Memory cache for Arrivals
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public class ArrivalHall {

    private final Set<Arrival> arrivals = new HashSet<>();
    private final Map<TransactionID, Arrival> arrivalMap = new WeakHashMap<>();

    private final Map<byte[], Long> arrivalFinished = new HashMap<>();  // ID -> timestamp
    private final ReadWriteLock arrivalLock = new ReentrantReadWriteLock();

    public Package insertFragment(Package fragment, SocketAddress source, SocketAddress destination) {
        Package pack = null;
        TransactionID sn = fragment.head.sn;
        byte[] snb = sn.getBytes();
        Lock writeLock = arrivalLock.writeLock();
        writeLock.lock();
        try {
            // check whether the task has already finished
            Long time = arrivalFinished.get(snb);
            if (time == null || time == 0) {
                Arrival task = arrivalMap.get(sn);
                if (task == null) {
                    // new arrival
                    task = new Arrival(sn, fragment.head.pages, source, destination);
                    arrivals.add(task);
                    arrivalMap.put(sn, task);
                }
                // insert
                pack = task.insert(fragment);
                if (pack != null) {
                    // all fragments received, remove this task
                    arrivals.remove(task);
                    arrivalMap.remove(sn);
                    // mark finished time
                    arrivalFinished.put(snb, (new Date()).getTime());
                }
            }
        } finally {
            writeLock.unlock();
        }
        return pack;
    }

    public void clearExpiredArrivals() {
        long now = (new Date()).getTime();
        Lock writeLock = arrivalLock.writeLock();
        writeLock.lock();
        try {
            Set<Arrival> expires = new HashSet<>();
            // get expired tasks
            for (Arrival task : arrivals) {
                if (task.isExpired(now)) {
                    expires.add(task);
                }
            }
            // remove expired tasks
            for (Arrival task : expires) {
                arrivals.remove(task);
                arrivalMap.remove(task.sn);
                // mark expired time
                arrivalFinished.put(task.sn.getBytes(), now);
            }
        } finally {
            writeLock.unlock();
        }
    }
}
