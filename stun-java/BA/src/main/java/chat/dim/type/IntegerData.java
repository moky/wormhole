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

/**
 *  Integer Data
 */
public interface IntegerData extends ByteArray {

    enum Endian {
        BIG_ENDIAN,    // Network Byte Order
        LITTLE_ENDIAN  // Host Byte Order
    }

    int getIntValue();

    long getLongValue();

    //
    //  Converting
    //

    /**
     *  Get long integer value from data buffer with range [offset, offset + size)
     *
     * @param buffer - data buffer
     * @param start  - data view offset
     * @param size   - data view size
     * @param endian - byte order
     * @return long value
     */
    static long getValue(byte[] buffer, int start, int size, Endian endian) {
        long result = 0;
        if (endian == Endian.LITTLE_ENDIAN) {
            // [12 34 56 78] => 0x78563412
            for (int pos = start + size - 1; pos >= start; --pos) {
                result = (result << 8) | (buffer[pos] & 0xFF);
            }
        } else if (endian == Endian.BIG_ENDIAN) {
            // [12 34 56 78] => 0x12345678
            int end = start + size;
            for (int pos = start; pos < end; ++pos) {
                result = (result << 8) | (buffer[pos] & 0xFF);
            }
        }
        return result;
    }
    static long getValue(ByteArray data, int start, int size, Endian endian) {
        assert start + size < data.getSize()
                : "out of range: start=" + start + ", size=" + size + ", view length=" + data.getSize();
        return getValue(data.getBuffer(), data.getOffset() + start, size, endian);
    }
    static long getValue(ByteArray data, int size, Endian endian) {
        assert size < data.getSize() : "out of range: size=" + size + ", view length=" + data.getSize();
        return getValue(data.getBuffer(), data.getOffset(), size, endian);
    }
    static long getValue(ByteArray data, Endian endian) {
        assert 0 < data.getSize() : "data empty";
        return getValue(data.getBuffer(), data.getOffset(), data.getSize(), endian);
    }

    /**
     *  Set long integer value into data buffer with size
     *
     * @param value  - integer value
     * @param buffer - data buffer
     * @param offset - data offset
     * @param size   - data size
     * @param endian - network order
     */
    static void setValue(long value, byte[] buffer, int offset, int size, Endian endian) {
        if (endian == Endian.LITTLE_ENDIAN) {
            // 0x12345678 => [78 56 34 12]
            int end = offset + size;
            for (int pos = offset; pos < end; ++pos) {
                buffer[pos] = (byte) (value & 0xFF);
                value >>= 8;
            }
        } else if (endian == Endian.BIG_ENDIAN) {
            // 0x12345678 => [12 34 56 78]
            for (int pos = offset + size - 1; pos >= offset; --pos) {
                buffer[pos] = (byte) (value & 0xFF);
                value >>= 8;
            }
        }
    }
    static void setValue(long value, MutableByteArray data, int start, int size, Endian endian) {
        data.setByte(start + size - 1, (byte) 0x00);
        setValue(value, data.getBuffer(), data.getOffset() + start, size, endian);
    }
    static void setValue(long value, MutableByteArray data, int size, Endian endian) {
        data.setByte(size - 1, (byte) 0x00);
        setValue(value, data.getBuffer(), data.getOffset(), size, endian);
    }
    static void setValue(long value, MutableByteArray data, Endian endian) {
        setValue(value, data.getBuffer(), data.getOffset(), data.getSize(), endian);
    }
}
