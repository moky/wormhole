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

import java.util.List;

public interface CachePool {

    /**
     *  Check whether cache is full
     *
     * @return true on full
     */
    boolean isCacheFull();

    /**
     *  Add received data to cache
     *
     * @param data - received data
     * @return ejected data when cache pool full
     */
    byte[] cache(byte[] data);

    /**
     *  Check received data (not remove)
     *
     * @return received data
     */
    byte[] received();

    /**
     *  Received data from pool with length (remove)
     *
     * @param length - data length to remove
     * @return remove data from the pool and return it
     */
    byte[] receive(int length);

    static byte[] slice(byte[] source, int start) {
        return slice(source, start, source.length);
    }
    static byte[] slice(byte[] source, int start, int end) {
        int length = end - start;
        byte[] data = new byte[length];
        System.arraycopy(source, start, data, 0, length);
        return data;
    }

    static byte[] concat(List<byte[]> array) {
        int count = array.size();
        int index;
        byte[] item;
        // 1. get buffer length
        int length = 0;
        for (index = 0; index < count; ++index) {
            item = array.get(index);
            length += item.length;
        }
        if (length == 0) {
            return null;
        }
        // 2. create buffer to copy data
        byte[] data = new byte[length];
        int offset = 0;
        // 3. get all data
        for (index = 0; index < count; ++index) {
            item = array.get(index);
            System.arraycopy(item, 0, data, offset, item.length);
            offset += item.length;
        }
        return data;
    }
}
