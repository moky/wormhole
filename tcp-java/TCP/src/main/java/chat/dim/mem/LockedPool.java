/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
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
package chat.dim.mem;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public final class LockedPool extends MemoryCache {

    private final ReadWriteLock lock = new ReentrantReadWriteLock();

    @Override
    public void push(byte[] pack) {
        Lock writeLock = lock.writeLock();
        writeLock.lock();
        try {
            super.push(pack);
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
            data = super.pop(maxLength);
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
            data = super.all();
        } finally {
            writeLock.unlock();
        }
        return data;
    }
}
