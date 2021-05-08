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
package chat.dim.mem;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public final class MemoryCache implements CachePool {

    // received packages
    private final ReadWriteLock lock = new ReentrantReadWriteLock();
    private final List<byte[]> packages = new ArrayList<>();
    private int count = 0;

    @Override
    public int length() {
        return count;
    }

    @Override
    public void push(byte[] pack) {
        assert pack != null && pack.length > 0: "data should not be empty";
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            packages.add(pack);
            count += pack.length;
        } finally {
            writeLock.unlock();
        }
    }

    @Override
    public byte[] pop(int maxLength) {
        byte[] data;
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            assert maxLength > 0 : "max length must greater than 0";
            assert packages.size() > 0 : "data empty, call 'get()/length()' to check data first";
            data = packages.remove(0);
            if (data.length > maxLength) {
                // push the remaining data back to the queue head
                packages.add(0, BytesArray.slice(data, maxLength, data.length));
                // cut the remaining data
                data = BytesArray.slice(data, 0, maxLength);
            }
            count -= data.length;
        } finally {
            writeLock.unlock();
        }
        return data;
    }

    @Override
    public byte[] all() {
        byte[] data;
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            int count = packages.size();
            if (count == 0) {
                data = null;
            } else if (count == 1) {
                data = packages.get(0);
            } else {
                data = BytesArray.concat(packages);
                packages.clear();
                packages.add(data);
            }
        } finally {
            writeLock.unlock();
        }
        return data;
    }
}
