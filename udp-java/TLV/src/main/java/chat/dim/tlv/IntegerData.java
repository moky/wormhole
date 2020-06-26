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

import java.nio.ByteOrder;

/**
 *  Integer data (network ordered)
 */
public class IntegerData extends Data {

    public final long value;

    public IntegerData(byte[] data, long value) {
        super(data);
        this.value = value;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (other instanceof IntegerData) {
            return equals(((IntegerData) other).value);
        }
        return false;
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
    //  Converting
    //

    private static long bytesToLongB(byte[] data) {
        long result = 0;
        int count = data.length;
        int index;
        for (index = 0; index < count; ++index) {
            result = (result << 8) | (data[index] & 0xFF);
        }
        return result;
    }
    private static long bytesToLongL(byte[] data) {
        long result = 0;
        int count = data.length;
        int index;
        for (index = count - 1; index >= 0; --index) {
            result = (result << 8) | (data[index] & 0xFF);
        }
        return result;
    }

    private static byte[] longToBytesB(long value, int length) {
        byte[] data = new byte[length];
        int index;
        for (index = length - 1; index >= 0; --index) {
            data[index] = (byte) (value & 0xFF);
            value >>= 8;
        }
        return data;
    }
    private static byte[] longToBytesL(long value, int length) {
        byte[] data = new byte[length];
        int index;
        for (index = 0; index < length; ++index) {
            data[index] = (byte) (value & 0xFF);
            value >>= 8;
        }
        return data;
    }

    // TODO: signed / unsigned int

    /**
     *  Convert bytes to int value
     *
     * @param data - bytes in network order
     * @return integer
     */
    public static int bytesToInt(byte[] data) {
        return (int) bytesToLongB(data);
    }
    public static long bytesToLong(byte[] data) {
        return bytesToLongB(data);
    }

    public static int bytesToInt(byte[] data, ByteOrder order) {
        if (order.equals(ByteOrder.BIG_ENDIAN)) {
            return (int) bytesToLongB(data);
        } else {
            return (int) bytesToLongL(data);
        }
    }
    public static long bytesToLong(byte[] data, ByteOrder order) {
        if (order.equals(ByteOrder.BIG_ENDIAN)) {
            return bytesToLongB(data);
        } else {
            return bytesToLongB(data);
        }
    }

    /**
     *  Convert int value to bytes
     *
     * @param value - int
     * @param length - size in bytes
     * @return bytes in network order
     */
    public static byte[] intToBytes(long value, int length) {
        return longToBytesB(value, length);
    }

    public static byte[] intToBytes(long value, int length, ByteOrder order) {
        if (order.equals(ByteOrder.BIG_ENDIAN)) {
            return longToBytesB(value, length);
        } else {
            return longToBytesL(value, length);
        }
    }
}
