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
public class Data implements Cloneable {

    // data view
    protected byte[] buffer;
    // buffer length
    protected int bufLength;
    // view offset
    protected int offset;
    // view length
    public final int length;

    /**
     *  Adjust position
     *
     * @param pos - position
     * @param len - length
     * @return adjust the position in range [0, len]
     */
    protected static int adjust(int pos, int len) {
        if (pos < 0) {
            pos += len;  // count from right hand
            if (pos < 0) {
                pos = 0; // too small
            }
        } else if (pos > len) {
            pos = len;   // too big
        }
        return pos;
    }

    /**
     *  Create data view with range [start, end)
     *
     * @param data  - data view
     * @param start - start position (include)
     * @param end   - end position (exclude)
     */
    public Data(byte[] data, int start, int end) {
        super();
        buffer = data;
        bufLength = data.length;

        // adjust positions
        start = adjust(start, bufLength);
        end = adjust(end, bufLength);

        offset = start;
        if (start < end) {
            length = end - start;
        } else {
            length = 0;  // end position should not smaller than start position
        }
    }

    /**
     *  Create data view with bytes
     *
     * @param data - bytes
     */
    public Data(byte[] data) {
        this(data, 0, data.length);
    }

    /**
     *  Clone data view
     *
     * @param data - same view
     */
    public Data(Data data) {
        this(data.buffer, data.offset, data.offset + data.length);
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof Data) {
            return equals((Data) other);
        }
        return this == other;
    }
    public boolean equals(Data other) {
        if (this == other) {
            return true;
        }
        return equals(other.buffer, other.offset, other.length);
    }
    public boolean equals(byte[] otherBuffer, int otherOffset, int otherLength) {
        if (otherBuffer == buffer) {
            if (otherLength == length && otherOffset == offset) {
                return true;
            }
        }
        if (otherLength != length) {
            return false;
        }
        int pos1 = offset + length - 1;
        int pos2 = otherLength + otherLength - 1;
        for (; pos1 >= offset; --pos1, --pos2) {
            if (buffer[pos1] != otherBuffer[pos2]) {
                return false;
            }
        }
        return true;
    }
    public boolean equals(byte[] other) {
        return equals(other, 0, other.length);
    }

    @Override
    public int hashCode() {
        if (offset == 0 && length == bufLength) {
            return Arrays.hashCode(buffer);
        } else {
            return Arrays.hashCode(slice(buffer, offset, offset + length));
        }
    }

    //
    //  To bytes
    //

    public byte[] getBytes() {
        return getBytes(0, length);
    }

    public byte[] getBytes(int start) {
        return getBytes(start, length);
    }

    public byte[] getBytes(int start, int end) {
        return slice(buffer, offset + start, offset + end);
    }

    //
    //  To another data
    //

    public Data slice(int start) {
        return slice(start, length);
    }

    public Data slice(int start, int end) {
        return new Data(buffer, offset + start, offset + end);
    }

    public Data concat(Data other) {
        if (other.buffer == buffer) {
            if (other.offset == offset + length) {
                // join the neighbour views
                return new Data(buffer, offset, offset + length + other.length);
            }
        }
        byte[] data = new byte[length + other.length];
        System.arraycopy(buffer, offset, data, 0, length);;
        System.arraycopy(other.buffer, other.offset, data, length, other.length);
        return new Data(data);
    }

    @Override
    public Data clone() throws CloneNotSupportedException {
        // deep copy
        byte[] data = new byte[length];
        System.arraycopy(buffer, offset, data, 0, length);
        Data copy = (Data) super.clone();
        copy.buffer = data;
        copy.bufLength = data.length;
        copy.offset = 0;
        return copy;
    }

    //
    //  bytes functions
    //

    public static byte[] slice(byte[] data, int start) {
        return slice(data, start, data.length);
    }

    public static byte[] slice(byte[] data, int start, int end) {
        int length = data.length;
        // adjust positions
        start = adjust(start, length);
        end = adjust(end, length);
        // check range
        if (start == 0 && end == length) {
            // same buffer
            return data;
        } else if (start >= end) {
            // empty buffer
            return new byte[0];
        }
        // copy sub-array
        byte[] buffer = new byte[end - start];
        System.arraycopy(data, start, buffer, 0, end - start);
        return buffer;
    }

    public static byte[] concat(byte[] array1, byte[] array2) {
        int len1 = array1.length;
        int len2 = array2.length;
        if (len1 == 0) {
            // array1 empty
            return array2;
        } else if (len2 == 0) {
            // array2 empty
            return array1;
        }
        byte[] buffer = new byte[len1 + len2];
        System.arraycopy(array1, 0, buffer, 0, len1);
        System.arraycopy(array2, 0, buffer, len1, len2);
        return buffer;
    }

    public static byte[] clone(byte[] data) {
        byte[] buffer = new byte[data.length];
        System.arraycopy(data, 0, buffer, 0, data.length);
        return buffer;
    }

    public static byte[] random(int length) {
        byte[] data = new byte[length];
        Random random = new Random();
        random.nextBytes(data);
        return data;
    }
}
