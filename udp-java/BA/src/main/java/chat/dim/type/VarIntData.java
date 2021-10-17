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
 *  Variable Integer
 */
public class VarIntData extends Data implements IntegerData {

    public final long value;

    public static final VarIntData ZERO = from(0);

    public VarIntData(ByteArray data, long value) {
        super(data);
        this.value = value;
    }

    public VarIntData(byte[] bytes, int offset, int size, long value) {
        super(bytes, offset, size);
        this.value = value;
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof IntegerData) {
            return value == ((IntegerData) other).getIntValue();
        } else {
            return super.equals(other);
        }
    }

    @Override
    public int hashCode() {
        return Long.hashCode(value);
    }

    @Override
    public java.lang.String toString() {
        return Long.toString(value);
    }

    @Override
    public int getIntValue() {
        return (int) value;
    }

    @Override
    public long getLongValue() {
        return value;
    }

    //
    //  Factories
    //

    public static VarIntData from(VarIntData data) {
        return data;
    }

    public static VarIntData from(ByteArray data) {
        return parse(data.getBuffer(), data.getOffset(), data.getSize());
    }

    public static VarIntData from(byte[] bytes) {
        return parse(bytes, 0, bytes.length);
    }

    public static VarIntData from(byte[] bytes, int start) {
        return parse(bytes, start, bytes.length - start);
    }

    public static VarIntData from(long value) {
        byte[] buffer = new byte[10];
        int length = setValue(value, buffer, 0, 10);
        return new VarIntData(buffer, 0, length, value);
    }

    //
    //  Converting
    //

    /**
     *  Deserialize VarIntData to integer value
     *
     * @param buffer - data buffer
     * @param offset - data view offset
     * @param size   - data view size
     * @return VarIntData
     */
    private static VarIntData parse(byte[] buffer, int offset, int size) {
        long value = 0;
        int bits = 0;
        int pos = offset;
        int end = offset + size;
        byte ch = (byte) 0x80;
        for (; (ch & 0x80) != 0; pos += 1, bits += 7) {
            if (pos >= end) {
                //throw new ArrayIndexOutOfBoundsException("out of range: [" + offset + ", " + length + ")");
                return null;
            }
            ch = buffer[pos];
            value |= (ch & 0x7FL) << bits;
        }
        return new VarIntData(buffer, offset, pos - offset, value);
    }

    /**
     *  Serialize integer value to VarIntData
     *
     * @param value  - integer value
     * @param buffer - data buffer
     * @param offset - data offset
     * @param length - data length limit
     * @return occupied data length
     */
    private static int setValue(long value, byte[] buffer, int offset, int length) {
        int pos;
        for (pos = offset; value > 0x7F; ++pos) {
            assert pos < (offset + length) : "out of range: [" + offset + ", " + length + ")";
            buffer[pos] = (byte) ((value & 0x7F) | 0x80);
            value >>= 7;
        }
        buffer[pos] = (byte) (value & 0x7F);
        return pos - offset + 1;
    }
}
