/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
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
package chat.dim.tcp;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class MemoryCache implements CachePool {

    /*  Max length of memory cache
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    public static int MAX_CACHE_LENGTH = 1024 * 1024 * 128;  // 128 MB

    // received packages
    private final List<byte[]> packages = new ArrayList<>();
    private final ReadWriteLock packageLock = new ReentrantReadWriteLock();

    @Override
    public boolean isCacheFull() {
        int length = 0;
        Lock readLock = packageLock.readLock();
        readLock.lock();
        try {
            for (byte[] pack : packages) {
                length += pack.length;
            }
        } finally {
            readLock.unlock();
        }
        return length >= MAX_CACHE_LENGTH;
    }

    @Override
    public byte[] cache(byte[] pack) {
        byte[] ejected = null;
        Lock writeLock = packageLock.writeLock();
        writeLock.lock();
        try {
            // 1. check memory cache status
            if (isCacheFull()) {
                // drop the first package
                ejected = packages.remove(0);
            }
            // 2. append the new package to the end
            packages.add(pack);
        } finally {
            writeLock.unlock();
        }
        return ejected;
    }

    @Override
    public byte[] received() {
        byte[] data;
        Lock writeLock = packageLock.writeLock();
        writeLock.lock();
        try {
            int count = packages.size();
            if (count == 0) {
                data = null;
            } else if (count == 1) {
                data = packages.get(0);
            } else {
                data = CachePool.concat(packages);
                packages.clear();
                packages.add(data);
            }
        } finally {
            writeLock.unlock();
        }
        return data;
    }

    @Override
    public byte[] receive(int length) {
        byte[] data;
        Lock writeLock = packageLock.writeLock();
        writeLock.lock();
        try {
            assert packages.size() > 0 : "data empty, call 'received()' to check data first";
            assert packages.get(0).length >= length : "data length error, call 'received()' first";
            data = packages.remove(0);
            if (data.length > length) {
                // push the remaining data back to the queue head
                packages.add(0, CachePool.slice(data, length));
                data = CachePool.slice(data, 0, length);
            }
        } finally {
            writeLock.unlock();
        }
        return data;
    }
}
