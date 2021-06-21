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
 *  Unsigned Short Integer (16-bytes)
 */
public class UInt16Data extends Data implements IntegerData {

    public final int value;

    public UInt16Data(UInt16Data data) {
        super(data);
        this.value = data.value;
    }

    public UInt16Data(ByteArray data, int value) {
        super(data);
        assert data.getLength() == 2 : "UInt16Data error: length=" + data.getLength();
        this.value = value;
    }

    public UInt16Data(ByteArray data, Endian endian) {
        super(data);
        assert data.getLength() == 2 : "UInt16Data error: length=" + data.getLength();
        this.value = getValue(data, endian);
    }

    public UInt16Data(byte[] bytes, int value) {
        super(bytes, 0, 2);
        assert bytes.length >= 2 : "UInt16Data error: length=" + bytes.length;
        this.value = value;
    }

    public UInt16Data(byte[] bytes, int offset, int value) {
        super(bytes, offset, 2);
        assert bytes.length >= (offset + 2) : "UInt16Data error: offset=" + offset + ", length=" + bytes.length;
        this.value = value;
    }

    public UInt16Data(byte[] bytes, Endian endian) {
        super(bytes, 0, 2);
        assert bytes.length >= 2 : "UInt16Data error: length=" + bytes.length;
        this.value = getValue(bytes, 0, endian);
    }

    public UInt16Data(byte[] bytes, int offset, Endian endian) {
        super(bytes, offset, 2);
        assert bytes.length >= (offset + 2) : "UInt16Data error: offset=" + offset + ", length=" + bytes.length;
        this.value = getValue(bytes, offset, endian);
    }

    public UInt16Data(int value, Endian endian) {
        super(getData(value, endian));
        this.value = value;
    }

    protected static int getValue(ByteArray data, Endian endian) {
        assert data.getLength() == 2 : "UInt16Data error: length=" + data.getLength();
        return (int) IntegerData.getValue(data, endian);
    }
    protected static int getValue(byte[] bytes, int offset, Endian endian) {
        assert bytes.length == offset + 2 : "UInt16Data error: offset=" + offset + ", length=" + bytes.length;
        return (int) IntegerData.getValue(bytes, offset, 2, endian);
    }
    protected static ByteArray getData(int value, Endian endian) {
        byte[] buffer = new byte[2];
        IntegerData.setValue(value, buffer, 0, 2, endian);
        return new Data(buffer);
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
        return Integer.hashCode(value);
    }

    @Override
    public String toString() {
        return Integer.toString(value);
    }

    @Override
    public int getIntValue() {
        return value;
    }

    @Override
    public long getLongValue() {
        return value;
    }

    //
    //  Factories
    //

    public static UInt16Data from(UInt16Data data) {
        return data;
    }

    public static UInt16Data from(ByteArray data, Endian endian) {
        if (data.getLength() < 2) {
            return null;
        } else if (data.getLength() > 2) {
            data = data.slice(0, 2);
        }
        return new UInt16Data(data, getValue(data, endian));
    }

    public static UInt16Data from(byte[] bytes, Endian endian) {
        if (bytes.length < 2) {
            return null;
        }
        return new UInt16Data(bytes, getValue(bytes, 0, endian));
    }

    public static UInt16Data from(byte[] bytes, int offset, Endian endian) {
        if (bytes.length < (offset + 2)) {
            return null;
        }
        return new UInt16Data(bytes, offset, getValue(bytes, offset, endian));
    }

    public static UInt16Data from(int value, Endian endian) {
        return new UInt16Data(getData(value, endian), value);
    }
}
