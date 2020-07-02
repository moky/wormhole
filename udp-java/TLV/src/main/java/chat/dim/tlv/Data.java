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

import java.nio.charset.Charset;
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
     *  Clone data view
     *
     * @param data - same view
     */
    public Data(Data data) {
        super();
        buffer = data.buffer;
        bufLength = data.bufLength;
        offset = data.offset;
        length = data.length;
    }

    /**
     *  Create data view with bytes
     *
     * @param bytes - data view
     */
    public Data(byte[] bytes) {
        this(bytes, 0, bytes.length);
    }

    /**
     *  Create data view with range [start, end)
     *
     * @param bytes - data view
     * @param start - start position (include)
     * @param end   - end position (exclude)
     */
    public Data(byte[] bytes, int start, int end) {
        super();
        buffer = bytes;
        bufLength = bytes.length;

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

    public Data(int capacity) {
        this(new byte[capacity], 0, capacity);
    }

    public final static Data ZERO = new Data(0);

    // adjust the position in range [0, len]
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
        int pos2 = otherOffset + otherLength - 1;
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
            return Arrays.hashCode(getBytes());
        }
    }

    @Override
    public String toString() {
        return new String(getBytes(), Charset.forName("UTF-8"));
    }

    public void copy(Data src, int srcPos, int destPos, int len) {
        // adjust positions
        srcPos = adjust(srcPos, src.length);
        destPos = adjust(destPos, length);
        assert len > 0 && (srcPos + len <= src.length) && (destPos + len <= length) : "copy length error: " + len;
        // copy buffer
        System.arraycopy(src.buffer, src.offset + srcPos, buffer, offset + destPos, len);
    }

    public void copy(byte[] src, int srcPos, int destPos, int len) {
        // adjust positions
        srcPos = adjust(srcPos, src.length);
        destPos = adjust(destPos, length);
        assert len > 0 && (srcPos + len <= src.length) && (destPos + len <= length) : "copy length error: " + len;
        // copy buffer
        System.arraycopy(src, srcPos, buffer, offset + destPos, len);
    }

    public void setByte(int index, byte value) {
        if (index >= 0 && index < length) {
            buffer[offset + index] = value;
        }
    }

    public byte getByte(int index) {
        return buffer[offset + index];
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
        // adjust positions
        start = offset + adjust(start, length);
        end = offset + adjust(end, length);
        // check range
        if (start == 0 && end == bufLength) {
            // same buffer
            return buffer;
        } else if (start >= end) {
            // empty buffer
            return new byte[0];
        }
        // copy sub-array
        byte[] bytes = new byte[end - start];
        System.arraycopy(buffer, start, bytes, 0, end - start);
        return bytes;
    }

    //
    //  To integer
    //

    public int getUInt8Value(int start) {
        int end = start + 1;
        if (start < 0 || end > length) {
            return 0;
        }
        return (int) IntegerData.longFromBytes(buffer, offset + start, offset + end);
    }

    public int getUInt16Value(int start) {
        int end = start + 2;
        if (start < 0 || end > length) {
            return 0;
        }
        return (int) IntegerData.longFromBytes(buffer, offset + start, offset + end);
    }

    public long getUInt32Value(int start) {
        int end = start + 4;
        if (start < 0 || end > length) {
            return 0;
        }
        return IntegerData.longFromBytes(buffer, offset + start, offset + end);
    }

    //
    //  To another data view
    //

    public Data slice(int start) {
        return slice(start, length);
    }

    public Data slice(int start, int end) {
        if (start == 0 && end == length) {
            return this;
        }
        return new Data(buffer, offset + start, offset + end);
    }

    public Data concat(Data other) {
        if (other.buffer == buffer) {
            if (other.offset == offset + length) {
                // join the neighbour views
                return new Data(buffer, offset, offset + length + other.length);
            }
        }
        byte[] bytes = new byte[length + other.length];
        System.arraycopy(buffer, offset, bytes, 0, length);
        System.arraycopy(other.buffer, other.offset, bytes, length, other.length);
        return new Data(bytes);
    }

    @Override
    public Data clone() throws CloneNotSupportedException {
        // deep copy
        byte[] bytes = new byte[length];
        System.arraycopy(buffer, offset, bytes, 0, length);
        Data copy = (Data) super.clone();
        copy.buffer = bytes;
        copy.bufLength = bytes.length;
        copy.offset = 0;
        return copy;
    }

    public static Data random(int length) {
        byte[] bytes = new byte[length];
        Random random = new Random();
        random.nextBytes(bytes);
        return new Data(bytes);
    }
}
