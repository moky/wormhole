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
import java.util.Random;

/**
 *  Data View
 */
public class Data implements Cloneable {

    /*
     * The fields of this class are package-private since MutableData
     * classes needs to access them.
     */

    // data view
    byte[] buffer;
    // buffer length
    int bufLength;
    // view offset
    int offset;
    // view length
    int length;

    public byte[] getBuffer() {
        return buffer;
    }

    public int getOffset() {
        return offset;
    }

    public int getLength() {
        return length;
    }

    public boolean isEmpty() {
        return length <= 0;
    }

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
     * @param bytes  - data view
     * @param offset - data view offset
     * @param length - data view length
     */
    public Data(byte[] bytes, int offset, int length) {
        super();
        this.buffer = bytes;
        this.bufLength = bytes.length;
        this.offset = offset;
        this.length = length;
    }

    public final static Data ZERO = new Data(new byte[0]);

    // adjust the position within range [0, len)
    static int adjust(int pos, int len) {
        if (pos < 0) {
            pos += len;    // count from right hand
            if (pos < 0) {
                return 0;  // too small
            }
        } else if (pos > len) {
            return len;    // too big
        }
        return pos;
    }

    static int adjustE(int pos, int len) {
        if (pos < 0) {
            pos += len;    // count from right hand
            if (pos < 0) {
                // too small
                throw new ArrayIndexOutOfBoundsException("error index: " + (pos - len) + ", length: " + len);
            }
        } else if (pos > len) {
            // too big
            throw new ArrayIndexOutOfBoundsException("error index: " + pos + ", length: " + len);
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
            // same buffer, checking range
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
        /*
        if (offset == 0 && length == bufLength) {
            return Arrays.hashCode(buffer);
        } else {
            return Arrays.hashCode(getBytes());
        }
         */
        int result = 1;
        int start = offset, end = offset + length;
        for (; start < end; ++start) {
            result = (result << 5) - result + buffer[start];
        }
        return result;
    }

    @Override
    public String toString() {
        return new String(getBytes(), Charset.forName("UTF-8"));
    }

    //
    //  Searching
    //

    public int find(byte value) {
        return find(value, 0, length);
    }

    public int find(byte value, int start) {
        return find(value, start, length);
    }

    public int find(byte value, int start, int end) {
        // adjust position
        start = offset + adjust(start, length);
        end = offset + adjust(end, length);
        for (; start < end; ++start) {
            if (buffer[start] == value) {
                // got it
                return start - offset;
            }
        }
        return -1;
    }

    public int find(int value, int start, int end) {
        return find((byte) (value & 0xFF), start, end);
    }

    public int find(int value, int start) {
        return find((byte) (value & 0xFF), start);
    }

    public int find(int value) {
        return find((byte) (value & 0xFF));
    }

    public int find(Data sub) {
        return find(sub, 0, length);
    }

    public int find(Data sub, int start) {
        return find(sub, start, length);
    }

    public int find(Data sub, int start, int end) {
        assert sub.length > 0 : "sub data length error";
        // adjust position
        start = adjust(start, length);
        end = adjust(end, length);
        if ((end - start) < sub.length) {
            return -1;
        }
        start += offset;
        end += offset - sub.length + 1;
        if (buffer == sub.buffer) {
            // same buffer
            if (start == sub.offset) {
                return sub.offset - offset;
            }
            /*
            if (start <= sub.offset && sub.offset < end) {
                // found in the range!
                return sub.offset - offset;
            }
             */
        }
        int index;
        for (; start < end; ++start) {
            for (index = 0; index < sub.length; ++index) {
                if (buffer[start + index] != sub.buffer[sub.offset + index]) {
                    // not match
                    break;
                }
            }
            if (index == sub.length) {
                // got it
                return start - offset;
            }
        }
        return -1;
    }

    public int find(byte[] sub, int start, int end) {
        return find(new Data(sub), start, end);
    }

    public int find(byte[] sub, int start) {
        return find(new Data(sub), start, length);
    }

    public int find(byte[] sub) {
        return find(new Data(sub), 0, length);
    }

    public byte getByte(int index) {
        // check position
        if (index < 0) {
            index += length;
            if (index < 0) {
                throw new ArrayIndexOutOfBoundsException("error index: " + (index - length) + ", length: " + length);
            }
        } else if (index >= length) {
            throw new ArrayIndexOutOfBoundsException("error index: " + index + ", length: " + length);
        }
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
            // whole buffer
            return buffer;
        } else if (start >= end) {
            // empty buffer
            return ZERO.getBytes();
        }
        // copy sub-array
        byte[] bytes = new byte[end - start];
        System.arraycopy(buffer, start, bytes, 0, end - start);
        return bytes;
    }

    //
    //  To integer
    //

    private long getIntegerValue(int start, int size) {
        assert size > 0 : "data size error";
        // check position
        start = adjustE(start, length);
        int end = start + size;
        if (end > length) {
            throw new ArrayIndexOutOfBoundsException("error index: " + start + ", size: " + size);
        }
        return IntegerData.longFromBytes(buffer, offset + start, offset + end);
    }

    public int getUInt8Value(int start) {
        return (int) getIntegerValue(start, 1);
    }

    public int getUInt16Value(int start) {
        return (int) getIntegerValue(start, 2);
    }

    public long getUInt32Value(int start) {
        return getIntegerValue(start, 4);
    }

    //
    //  To another data view
    //

    public Data slice(int start) {
        return slice(start, length);
    }

    public Data slice(int start, int end) {
        // adjust positions
        start = adjust(start, length);
        end = adjust(end, length);
        if (start == 0 && end == length) {
            return this;
        } else if (start >= end) {
            return ZERO;
        }
        return new Data(buffer, offset + start, end - start);
    }

    public Data concat(Data other) {
        return concat(other, 0, other.length);
    }

    public Data concat(Data other, int start) {
        return concat(other, start, other.length);
    }

    public Data concat(Data other, int start, int end) {
        // adjust positions
        start = adjust(start, other.length);
        end = adjust(end, other.length);
        int copyLen = end - start;
        if (copyLen < 0) {
            throw new IndexOutOfBoundsException("error index: " + start + ", " + end + ", length: " + other.length);
        } else if (copyLen == 0) {
            // other view empty, return this view
            return this;
        } else if (length == 0) {
            // this view empty, return other view
            return other.slice(start, end);
        } else if (buffer == other.buffer) {
            // same buffer
            if (offset + length == other.offset + start) {
                // join the neighbour views
                return new Data(buffer, offset, length + copyLen);
            }
        }
        // join two data to new buffer
        byte[] joined = new byte[length + copyLen];
        System.arraycopy(buffer, offset, joined, 0, length);
        System.arraycopy(other.buffer, other.offset + start, joined, length, copyLen);
        return new Data(joined);
    }

    public Data concat(byte[] bytes, int start, int end) {
        return concat(new Data(bytes), start, end);
    }

    public Data concat(byte[] bytes, int start) {
        return concat(bytes, start, bytes.length);
    }

    public Data concat(byte[] bytes) {
        return concat(bytes, 0, bytes.length);
    }

    @Override
    public Data clone() {
        // deep copy
        Data copy;
        try {
            copy = (Data) super.clone();
        } catch (CloneNotSupportedException e) {
            e.printStackTrace();
            return null;
        }
        byte[] bytes = new byte[length];
        System.arraycopy(buffer, offset, bytes, 0, length);
        copy.buffer = bytes;
        copy.bufLength = length;
        copy.offset = 0;
        copy.length = length;
        return copy;
    }

    public MutableData mutableCopy() {
        byte[] bytes = new byte[length];
        System.arraycopy(buffer, offset, bytes, 0, length);
        return new MutableData(bytes);
    }

    public static Data random(int length) {
        byte[] bytes = new byte[length];
        Random random = new Random();
        random.nextBytes(bytes);
        return new Data(bytes);
    }
}
