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

/**
 *  Integer data (network ordered)
 */
public class IntegerData extends Data {

    public final long value;

    public IntegerData(Data data, long value) {
        super(data);
        this.value = value;
    }

    public IntegerData(byte[] data, long value) {
        super(data);
        this.value = value;
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof IntegerData) {
            return value == ((IntegerData) other).value;
        }
        return this == other;
    }
    public boolean equals(int other) {
        return value == other;
    }
    public boolean equals(long other) {
        return value == other;
    }

    @Override
    public int hashCode() {
        return Long.hashCode(value);
    }

    public int getIntValue() {
        return (int) value;
    }
    public long getLongValue() {
        return value;
    }

    //
    //  bytes functions
    //

    protected static long longFromBytes(byte[] data) {
        return longFromBytes(data, 0, data.length);
    }
    protected static long longFromBytes(byte[] data, int length) {
        return longFromBytes(data, 0, length);
    }
    protected static long longFromBytes(byte[] data, int start, int end) {
        // adjust positions
        start = adjust(start, data.length);
        end = adjust(end, data.length);
        if (start >= end) {
            return 0;
        }
        long result = 0;
        for (; start < end; ++start) {
            result = (result << 8) | (data[start] & 0xFF);
        }
        return result;
    }

    protected static byte[] bytesFromLong(long value, int length) {
        byte[] data = new byte[length];
        int index;
        for (index = length - 1; index >= 0; --index) {
            data[index] = (byte) (value & 0xFF);
            value >>= 8;
        }
        return data;
    }
}
