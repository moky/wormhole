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

public class MemoryPool implements CachePool {

    // received packages
    private final List<byte[]> packages = new ArrayList<>();
    private int occupied = 0;

    @Override
    public int length() {
        return occupied;
    }

    @Override
    public void push(byte[] data) {
        assert data != null && data.length > 0: "data should not be empty";
        packages.add(data);
        occupied += data.length;
    }

    @Override
    public byte[] shift(int maxLength) {
        assert packages.size() > 0 : "pool empty, call 'length()' to check data first";
        byte[] data = packages.remove(0);
        if (0 < maxLength && maxLength < data.length) {
            // push the remaining data back to the queue head
            packages.add(0, slice(data, maxLength));
            // cut the remaining data
            data = slice(data, 0, maxLength);
        }
        occupied -= data.length;
        return data;
    }

    //
    //  ByteArray
    //
    public static byte[] slice(byte[] source, int start) {
        return slice(source, start, source.length);
    }
    public static byte[] slice(byte[] source, int start, int end) {
        int length = end - start;
        byte[] data = new byte[length];
        System.arraycopy(source, start, data, 0, length);
        return data;
    }
}
