/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
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
package chat.dim.tlv;

import java.util.Arrays;
import java.util.Random;

/**
 *  Data in bytes
 */
public class Data {

    public final byte[] data;
    public final int length;

    public Data(byte[] data) {
        super();
        this.data = data;
        this.length = data.length;
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof Data) {
            return equals(((Data) other).data);
        }
        return this == other;
    }
    public boolean equals(byte[] other) {
        if (other.length != data.length) {
            return false;
        }
        int pos = other.length - 1;
        for (; pos >= 0; --pos) {
            if (other[pos] != data[pos]) {
                return false;
            }
        }
        return true;
    }

    @Override
    public int hashCode() {
        return Arrays.hashCode(data);
    }

    //
    //  functions
    //

    public static byte[] slice(byte[] data, int start) {
        return slice(data, start, data.length);
    }

    public static byte[] slice(byte[] data, int start, int end) {
        int length = data.length;
        // check start position
        if (start < 0) {
            start += length;
            if (start < 0) {
                start = 0;
            }
        } else if (start >= length) {
            return new byte[0];
        }
        // check end position
        if (end < 0) {
            end += length;
            if (end <= 0) {
                return new byte[0];
            }
        } else if (end > length) {
            end = length;
        }
        // check range
        if (start >= end) {
            return new byte[0];
        }
        /*
        if (start == 0 && end == data.length) {
            return data;
        }
         */
        // copy sub-array
        byte[] buffer = new byte[end - start];
        System.arraycopy(data, start, buffer, 0, end - start);
        return buffer;
    }

    public static byte[] concat(byte[] array1, byte[] array2) {
        byte[] buffer = new byte[array1.length + array2.length];
        System.arraycopy(array1, 0, buffer, 0, array1.length);
        System.arraycopy(array2, 0, buffer, array1.length, array2.length);
        return buffer;
    }

    public static byte[] randomBytes(int length) {
        byte[] data = new byte[length];
        Random random = new Random();
        random.nextBytes(data);
        return data;
    }
}
