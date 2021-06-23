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

import chat.dim.type.ByteArray;

public class MemoryCache implements CachePool {

    // received packages
    private final List<ByteArray> packages = new ArrayList<>();
    private int occupied = 0;

    @Override
    public int length() {
        return occupied;
    }

    @Override
    public void push(ByteArray data) {
        assert data != null && data.getSize() > 0: "data should not be empty";
        packages.add(data);
        occupied += data.getSize();
    }

    @Override
    public ByteArray shift(int maxLength) {
        assert maxLength > 0 : "max length must greater than 0";
        assert packages.size() > 0 : "pool empty, call 'length()' to check data first";
        ByteArray data = packages.remove(0);
        if (data.getSize() > maxLength) {
            // push the remaining data back to the queue head
            packages.add(0, data.slice(maxLength));
            // cut the remaining data
            data = data.slice(0, maxLength);
        }
        occupied -= data.getSize();
        return data;
    }
}
