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

    public VarIntData(VarIntData data) {
        super(data);
        this.value = data.value;
    }

    public VarIntData(ByteArray data, long value) {
        super(data);
        this.value = value;
    }

    public VarIntData(byte[] bytes, long value) {
        super(bytes);
        this.value = value;
    }

    @Override
    public int getIntValue() {
        return (int) value;
    }

    @Override
    public long getLongValue() {
        return value;
    }

    public static VarIntData from(ByteArray data) {
        return getValue(data.getBuffer(), data.getOffset(), data.getLength());
    }

    public static VarIntData from(ByteArray data, int start) {
        return getValue(data.getBuffer(), data.getOffset() + start, data.getLength() - start);
    }

    public static VarIntData from(byte[] bytes) {
        return getValue(bytes, 0, bytes.length);
    }

    public static VarIntData from(byte[] bytes, int start) {
        return getValue(bytes, start, bytes.length - start);
    }

    public static VarIntData from(long value) {
        byte[] buffer = new byte[10];
        int length = setValue(value, buffer, 0, 10);
        Data data = new Data(buffer, 0, length);
        return new VarIntData(data, value);
    }

    //
    //  Converting
    //

    /**
     *  Deserialize VarIntData to integer value
     *
     * @param buffer - data buffer
     * @param offset - data offset
     * @param length - data length limit
     * @return VarIntData
     */
    private static VarIntData getValue(byte[] buffer, int offset, int length) {
        long value = 0;
        int pos, bits;
        byte ch = (byte) 0x80;
        for (pos = offset, bits = 0; (ch & 0x80) != 0; pos += 1, bits += 7) {
            assert pos < (offset + length) : "out of range: [" + offset + ", " + length + ")";
            ch = buffer[pos];
            value |= (ch & 0x7FL) << bits;
        }
        Data data = new Data(buffer, offset, pos - offset);
        return new VarIntData(data, value);
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
