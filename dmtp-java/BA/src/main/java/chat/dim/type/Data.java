/* license: https://mit-license.org
 *
 *  BA: Byte Array
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
package chat.dim.type;

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
    byte[] buffer;  // data view
    int offset;     // view offset
    int length;     // view length

    public final static Data ZERO = new Data(new byte[0], 0, 0);

    /**
     *  Create data view with range [start, end)
     *
     * @param buffer - data view
     * @param offset - data view offset
     * @param length - data view length
     */
    public Data(byte[] buffer, int offset, int length) {
        super();
        this.buffer = buffer;
        this.offset = offset;
        this.length = length;
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
     *  Clone data view
     *
     * @param data - other data view
     */
    public Data(Data data) {
        this(data.buffer, data.offset, data.length);
    }

    public byte[] getBuffer() {
        return buffer;
    }

    public int getOffset() {
        return offset;
    }

    public int getLength() {
        return length;
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof Data) {
            return equals((Data) other);
        } else {
            return false;
        }
    }
    public boolean equals(Data other) {
        return this == other || equals(other.getBuffer(), other.getOffset(), other.getLength());
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
        //return Arrays.hashCode(getBytes());
        int result = 1;
        int start = offset, end = offset + length;
        for (; start < end; ++start) {
            result = (result << 5) - result + buffer[start];
        }
        return result;
    }

    @Override
    public String toString() {
        //noinspection CharsetObjectCanBeUsed
        return new String(getBytes(), Charset.forName("UTF-8"));
    }

    /**
     *  Search value in range [start, end)
     *
     * @param value - element value
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return -1 on not found
     */
    public int find(byte value, int start, int end) {
        return DataUtils.find(this, value, DataUtils.adjust(start, length), DataUtils.adjust(end, length));
    }
    public int find(byte value, int start) {
        return DataUtils.find(this, value, DataUtils.adjust(start, length), length);
    }
    public int find(byte value) {
        return DataUtils.find(this, value, 0, length);
    }

    public int find(int value, int start, int end) {
        return DataUtils.find(this, (byte) (value & 0xFF),
                DataUtils.adjust(start, length), DataUtils.adjust(end, length));
    }
    public int find(int value, int start) {
        return DataUtils.find(this, (byte) (value & 0xFF), DataUtils.adjust(start, length), length);
    }
    public int find(int value) {
        return DataUtils.find(this, (byte) (value & 0xFF), 0, length);
    }

    /**
     *  Search sub bytes in range [start, end)
     *
     * @param bytes - sub view
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return -1 on not found
     */
    public int find(byte[] bytes, int start, int end) {
        return DataUtils.find(this, bytes, 0, bytes.length,
                DataUtils.adjust(start, length), DataUtils.adjust(end, length));
    }
    public int find(byte[] bytes, int start) {
        return DataUtils.find(this, bytes, 0, bytes.length,
                DataUtils.adjust(start, length), length);
    }
    public int find(byte[] bytes) {
        return DataUtils.find(this, bytes, 0, bytes.length, 0, length);
    }

    public int find(Data sub, int start, int end) {
        return DataUtils.find(this, sub.getBuffer(), sub.getOffset(), sub.getLength(),
                DataUtils.adjust(start, length), DataUtils.adjust(end, length));
    }
    public int find(Data sub, int start) {
        return DataUtils.find(this, sub.getBuffer(), sub.getOffset(), sub.getLength(),
                DataUtils.adjust(start, length), length);
    }
    public int find(Data sub) {
        return DataUtils.find(this, sub.getBuffer(), sub.getOffset(), sub.getLength(), 0, length);
    }

    //
    //  Reading
    //

    /**
     *  Get item value with position
     *
     * @param index - item position
     * @return item value
     */
    public byte getByte(int index) {
        // check position
        if (index < 0) {
            index += length;  // count from right hand
            if (index < 0) {  // too small
                throw new ArrayIndexOutOfBoundsException("error index: " + (index - length) + ", length: " + length);
            }
        } else if (index >= length) {
            throw new ArrayIndexOutOfBoundsException("error index: " + index + ", length: " + length);
        }
        return buffer[offset + index];
    }

    public byte[] getBytes() {
        return DataUtils.getBytes(this, 0, length);
    }

    public byte[] getBytes(int start) {
        return DataUtils.getBytes(this, DataUtils.adjust(start, length), length);
    }

    public byte[] getBytes(int start, int end) {
        return DataUtils.getBytes(this, DataUtils.adjust(start, length), DataUtils.adjust(end, length));
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
        return DataUtils.slice(this, DataUtils.adjust(start, length), DataUtils.adjust(end, length));
    }

    public Data slice(int start) {
        return DataUtils.slice(this, DataUtils.adjust(start, length), length);
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
            result = DataUtils.concat(result, other);
        }
        return result;
    }

    public Data concat(byte[]... others) {
        Data result = this;
        for (byte[] bytes : others) {
            result = DataUtils.concat(result, new Data(bytes));
        }
        return result;
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
