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
public class Data implements ByteArray, Cloneable {

    /*
     * The fields of this class are package-private since MutableData
     * classes needs to access them.
     */
    byte[] buffer;  // data buffer
    int offset;     // data view offset
    int size;       // data view size

    public final static Data ZERO = new Data(new byte[0]);

    /**
     *  Create data view with range [start, end)
     *
     * @param buffer - data buffer
     * @param offset - data view offset
     * @param size   - data view size
     */
    public Data(byte[] buffer, int offset, int size) {
        super();
        this.buffer = buffer;
        this.offset = offset;
        this.size = size;
        assert buffer.length >= (offset + size) : "range error: " + buffer.length + " < " + offset + " + " + size;
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
    public Data(ByteArray data) {
        this(data.getBuffer(), data.getOffset(), data.getSize());
    }

    @Override
    public byte[] getBuffer() {
        return buffer;
    }

    @Override
    public int getOffset() {
        return offset;
    }

    @Override
    public int getSize() {
        return size;
    }

    @Override
    public boolean equals(Object other) {
        if (other == this) {
            return true;
        } else if (other instanceof ByteArray) {
            return equals((ByteArray) other);
        } else if (other instanceof byte[]) {
            return equals((byte[]) other);
        } else {
            return false;
        }
    }
    @Override
    public boolean equals(ByteArray other) {
        return this == other || equals(other.getBuffer(), other.getOffset(), other.getSize());
    }
    @Override
    public boolean equals(byte[] other) {
        return equals(other, 0, other.length);
    }
    @Override
    public boolean equals(byte[] otherBuffer, int otherOffset, int otherCount) {
        if (otherCount != size) {
            return false;
        } else if (otherBuffer == buffer && otherOffset == offset) {
            return true;
        }
        int pos1 = offset + size - 1;
        int pos2 = otherOffset + otherCount - 1;
        for (; pos1 >= offset; --pos1, --pos2) {
            if (buffer[pos1] != otherBuffer[pos2]) {
                return false;
            }
        }
        return true;
    }

    @Override
    public int hashCode() {
        //return Arrays.hashCode(getBytes());
        int result = 1;
        int start = offset, end = offset + size;
        for (; start < end; ++start) {
            result = (result << 5) - result + buffer[start];
        }
        return result;
    }

    @Override
    public java.lang.String toString() {
        return new java.lang.String(getBytes());
        //return toHexString();
    }

    @Override
    public java.lang.String toHexString() {
        return ByteArray.hexEncode(buffer, offset, size);
    }

    //
    //  Searching
    //

    @Override
    public int find(byte value, int start, int end) {
        return ByteArray.find(this, value, ByteArray.adjust(start, size), ByteArray.adjust(end, size));
    }
    @Override
    public int find(byte value, int start) {
        return ByteArray.find(this, value, ByteArray.adjust(start, size), size);
    }
    @Override
    public int find(byte value) {
        return ByteArray.find(this, value, 0, size);
    }

    @Override
    public int find(int value, int start, int end) {
        return ByteArray.find(this, (byte) (value & 0xFF),
                ByteArray.adjust(start, size), ByteArray.adjust(end, size));
    }
    @Override
    public int find(int value, int start) {
        return ByteArray.find(this, (byte) (value & 0xFF), ByteArray.adjust(start, size), size);
    }
    @Override
    public int find(int value) {
        return ByteArray.find(this, (byte) (value & 0xFF), 0, size);
    }

    @Override
    public int find(byte[] bytes, int start, int end) {
        return ByteArray.find(this, bytes, 0, bytes.length,
                ByteArray.adjust(start, size), ByteArray.adjust(end, size));
    }
    @Override
    public int find(byte[] bytes, int start) {
        return ByteArray.find(this, bytes, 0, bytes.length,
                ByteArray.adjust(start, size), size);
    }
    @Override
    public int find(byte[] bytes) {
        return ByteArray.find(this, bytes, 0, bytes.length, 0, size);
    }

    @Override
    public int find(ByteArray sub, int start, int end) {
        return ByteArray.find(this, sub.getBuffer(), sub.getOffset(), sub.getSize(),
                ByteArray.adjust(start, size), ByteArray.adjust(end, size));
    }
    @Override
    public int find(ByteArray sub, int start) {
        return ByteArray.find(this, sub.getBuffer(), sub.getOffset(), sub.getSize(),
                ByteArray.adjust(start, size), size);
    }
    @Override
    public int find(ByteArray sub) {
        return ByteArray.find(this, sub.getBuffer(), sub.getOffset(), sub.getSize(), 0, size);
    }

    //
    //  Reading
    //

    @Override
    public byte getByte(int index) {
        // check position
        index = ByteArray.adjustE(index, size);
        if (index >= size) {
            throw new ArrayIndexOutOfBoundsException("error index: " + index + ", size: " + size);
        }
        return buffer[offset + index];
    }

    @Override
    public byte[] getBytes() {
        return ByteArray.slice(buffer, offset, offset + size);
    }

    @Override
    public byte[] getBytes(int start) {
        return ByteArray.slice(buffer,
                offset + ByteArray.adjust(start, size),
                offset + size);
    }

    @Override
    public byte[] getBytes(int start, int end) {
        return ByteArray.slice(buffer,
                offset + ByteArray.adjust(start, size),
                offset + ByteArray.adjust(end, size));
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
    @Override
    public ByteArray slice(int start, int end) {
        return ByteArray.slice(this, ByteArray.adjust(start, size), ByteArray.adjust(end, size));
    }

    @Override
    public ByteArray slice(int start) {
        return ByteArray.slice(this, ByteArray.adjust(start, size), size);
    }

    /**
     *  Combines two or more data.
     *
     * @param others - other data
     * @return combined data view
     */
    @Override
    public ByteArray concat(ByteArray... others) {
        ByteArray result = this;
        for (ByteArray item : others) {
            if (item == null) {
                continue;
            }
            result = ByteArray.concat(result, item);
        }
        return result;
    }

    @Override
    public ByteArray concat(byte[]... others) {
        ByteArray result = this;
        for (byte[] item : others) {
            if (item == null) {
                continue;
            }
            result = ByteArray.concat(result, new Data(item));
        }
        return result;
    }

    @Override
    public Data clone() throws CloneNotSupportedException {
        Data copy = (Data) super.clone();
        byte[] bytes = new byte[size];
        System.arraycopy(buffer, offset, bytes, 0, size);
        copy.buffer = bytes;
        copy.offset = 0;
        copy.size = size;
        return copy;
    }

    public MutableData mutableCopy() {
        byte[] bytes = new byte[size];
        System.arraycopy(buffer, offset, bytes, 0, size);
        return new MutableData(bytes);
    }

    public static ByteArray random(int length) {
        byte[] bytes = new byte[length];
        Random random = new Random();
        random.nextBytes(bytes);
        return new Data(bytes);
    }
}
