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

    /**
     *  Clone data view
     *
     * @param data - same view
     */
    public Data(Data data) {
        super();
        buffer = data.buffer;
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
        this.offset = offset;
        this.length = length;
    }

    public final static Data ZERO = new Data(new byte[0]);

    @Override
    public boolean equals(Object other) {
        if (other instanceof Data) {
            return equals((Data) other);
        } else {
            return false;
        }
    }
    public boolean equals(Data other) {
        return this == other || equals(other.buffer, other.offset, other.length);
    }
    public boolean equals(byte[] otherBuffer, int otherOffset, int otherLength) {
        if (otherLength != length) {
            return false;
        } else if (otherBuffer == buffer && otherOffset == offset) {
            return true;
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
        if (offset == 0 && length == buffer.length) {
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

    //
    //  Searching
    //

    /**
     *  Search value in range [start, end)
     *
     * @param value - element value
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return -1 on not found
     */
    private int findValue(byte value, int start, int end) {
        start += offset;
        end += offset;
        for (; start < end; ++start) {
            if (buffer[start] == value) {
                // got it
                return start - offset;
            }
        }
        return -1;
    }

    public int find(byte value) {
        return findValue(value, 0, length);
    }

    public int find(byte value, int start) {
        start = adjust(start, length);
        return findValue(value, start, length);
    }

    public int find(byte value, int start, int end) {
        start = adjust(start, length);
        end = adjust(end, length);
        return findValue(value, start, end);
    }

    public int find(int value) {
        return findValue((byte) (value & 0xFF), 0, length);
    }

    public int find(int value, int start) {
        start = adjust(start, length);
        return findValue((byte) (value & 0xFF), start, length);
    }

    public int find(int value, int start, int end) {
        start = adjust(start, length);
        end = adjust(end, length);
        return findValue((byte) (value & 0xFF), start, end);
    }

    /**
     *  Search sub data in range [start, end)
     *
     * @param sub   - sub data
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return -1 on not found
     */
    private int findSub(Data sub, int start, int end) {
        assert sub.length > 0 : "sub data length error";
        assert end >= start : "range error: " + start + ", " + end;
        if ((end - start) < sub.length) {
            return -1;
        }
        start += offset;
        end += offset - sub.length + 1;
        if (buffer == sub.buffer) {
            // same buffer
            if (start == sub.offset) {
                return start - offset;
            }
            // NOTICE: if (start < sub.offset < end), then the position (sub.offset - this.offset) is right,
            //         but we cannot confirm this is the first position it appeared,
            //         so we still need to do searching.
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

    public int find(Data sub) {
        return findSub(sub, 0, length);
    }

    public int find(Data sub, int start) {
        start = adjust(start, length);
        return findSub(sub, start, length);
    }

    public int find(Data sub, int start, int end) {
        start = adjust(start, length);
        end = adjust(end, length);
        return findSub(sub, start, end);
    }

    public int find(byte[] sub) {
        return findSub(new Data(sub), 0, length);
    }

    public int find(byte[] sub, int start) {
        start = adjust(start, length);
        return findSub(new Data(sub), start, length);
    }

    public int find(byte[] sub, int start, int end) {
        start = adjust(start, length);
        end = adjust(end, length);
        return findSub(new Data(sub), start, end);
    }

    /**
     *  Get item value with position
     *
     * @param index - item position
     * @return item value
     */
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

    /**
     *  Get bytes within range [start, end)
     *
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return sub bytes
     */
    private byte[] getSubBytes(int start, int end) {
        start += offset;
        end += offset;
        // check range
        if (start == 0 && end == buffer.length) {
            // whole buffer
            return buffer;
        } else if (start < end) {
            // copy sub-array
            int copyLen = end - start;
            byte[] bytes = new byte[copyLen];
            System.arraycopy(buffer, start, bytes, 0, copyLen);
            return bytes;
        } else {
            // empty buffer
            return ZERO.getBytes();
        }
    }

    public byte[] getBytes() {
        return getSubBytes(0, length);
    }

    public byte[] getBytes(int start) {
        start = offset + adjust(start, length);
        return getSubBytes(start, length);
    }

    public byte[] getBytes(int start, int end) {
        start = offset + adjust(start, length);
        end = offset + adjust(end, length);
        return getSubBytes(start, end);
    }

    //
    //  To integer
    //

    private long getIntegerValue(int start, int size) {
        assert size > 0 : "data size error";
        // adjust start position
        if (start < 0) {
            start += length;  // count from right hand
            if (start < 0) {  // too small
                throw new ArrayIndexOutOfBoundsException("error index: " + (start - length) + ", length: " + length);
            }
        }
        // check end position
        int end = start + size;
        if (end > length) {
            throw new ArrayIndexOutOfBoundsException("error index: " + start + " + " + size + ", length: " + length);
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

    /**
     *  Get sub data within range [start, end)
     *
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return sub data
     */
    public Data slice(int start, int end) {
        start = adjust(start, length);
        end = adjust(end, length);
        return slice(this, start, end);
    }

    public Data slice(int start) {
        start = adjust(start, length);
        return slice(this, start, length);
    }

    private static Data slice(Data data, int start, int end) {
        if (start == 0 && end == data.length) {
            // whole data
            return data;
        } else if (start < end) {
            // sub view
            return new Data(data.buffer, data.offset + start, end - start);
        } else {
            // error
            return ZERO;
        }
    }

    /**
     *  Combines two or more data.
     *
     * @param others - other data
     * @return combined data view
     */
    public Data concat(Data... others) {
        Data result = this;
        for (Data other : others) {
            result = concat(result, other);
        }
        return result;
    }

    public Data concat(byte[]... others) {
        Data result = this;
        Data other;
        for (byte[] bytes : others) {
            other = new Data(bytes);
            result = concat(result, other);
        }
        return result;
    }

    private static Data concat(Data left, Data right) {
        if (left.length == 0) {
            return right;
        } else if (right.length == 0) {
            return left;
        } else if (left.buffer == right.buffer && (left.offset + left.length) == right.offset) {
            // sticky data
            return new Data(left.buffer, left.offset, left.length + right.length);
        } else {
            byte[] joined = new byte[left.length + right.length];
            System.arraycopy(left.buffer, left.offset, joined, 0, left.length);
            System.arraycopy(right.buffer, right.offset, joined, left.length, right.length);
            return new Data(joined);
        }
    }

    @Override
    public Data clone() {
        Data copy;
        try {
            copy = (Data) super.clone();
        } catch (CloneNotSupportedException e) {
            e.printStackTrace();
            return null;
        }
        copy.buffer = buffer;
        copy.offset = offset;
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
