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
 *  Unsigned Integer (32-bytes)
 */
public class UInt32Data extends Data implements IntegerData {

    public final long value;

    public UInt32Data(UInt32Data data) {
        super(data);
        this.value = data.value;
    }

    public UInt32Data(ByteArray data, long value) {
        super(data);
        assert data.getLength() == 4 : "UInt32Data error: length=" + data.getLength();
        this.value = value;
    }

    public UInt32Data(ByteArray data, Endian endian) {
        super(data);
        assert data.getLength() == 4 : "UInt32Data error: length=" + data.getLength();
        this.value = getValue(data, endian);
    }

    public UInt32Data(byte[] bytes, long value) {
        super(bytes, 0, 4);
        assert bytes.length >= 4 : "UInt32Data error: length=" + bytes.length;
        this.value = value;
    }

    public UInt32Data(byte[] bytes, int offset, int value) {
        super(bytes, offset, 4);
        assert bytes.length >= (offset + 4) : "UInt32Data error: offset=" + offset + ", length=" + bytes.length;
        this.value = value;
    }

    public UInt32Data(byte[] bytes, Endian endian) {
        super(bytes, 0, 4);
        assert bytes.length >= 4 : "UInt32Data error: length=" + bytes.length;
        this.value = getValue(bytes, 0, endian);
    }

    public UInt32Data(byte[] bytes, int offset, Endian endian) {
        super(bytes, offset, 4);
        assert bytes.length >= (offset + 4) : "UInt32Data error: offset=" + offset + ", length=" + bytes.length;
        this.value = getValue(bytes, offset, endian);
    }

    public UInt32Data(int value, Endian endian) {
        super(getData(value, endian));
        this.value = value;
    }

    protected static int getValue(ByteArray data, Endian endian) {
        assert data.getLength() == 4 : "UInt32Data error: length=" + data.getLength();
        return (int) IntegerData.getValue(data, endian);
    }
    protected static int getValue(byte[] bytes, int offset, Endian endian) {
        assert bytes.length == offset + 4 : "UInt32Data error: offset=" + offset + ", length=" + bytes.length;
        return (int) IntegerData.getValue(bytes, offset, 2, endian);
    }
    protected static ByteArray getData(int value, Endian endian) {
        byte[] buffer = new byte[4];
        IntegerData.setValue(value, buffer, 0, 4, endian);
        return new Data(buffer);
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof IntegerData) {
            return value == ((IntegerData) other).getLongValue();
        } else {
            return super.equals(other);
        }
    }

    @Override
    public int hashCode() {
        return Long.hashCode(value);
    }

    @Override
    public String toString() {
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

    public static UInt32Data from(UInt32Data data) {
        return data;
    }

    public static UInt32Data from(ByteArray data, Endian endian) {
        if (data.getLength() < 4) {
            return null;
        } else if (data.getLength() > 4) {
            data = data.slice(0, 4);
        }
        return new UInt32Data(data, getValue(data, endian));
    }

    public static UInt32Data from(byte[] bytes, Endian endian) {
        if (bytes.length < 4) {
            return null;
        }
        return new UInt32Data(bytes, getValue(bytes, 0, endian));
    }

    public static UInt32Data from(byte[] bytes, int offset, Endian endian) {
        if (bytes.length < (offset + 4)) {
            return null;
        }
        return new UInt32Data(bytes, offset, getValue(bytes, offset, endian));
    }

    public static UInt32Data from(int value, Endian endian) {
        return new UInt32Data(getData(value, endian), value);
    }
}
