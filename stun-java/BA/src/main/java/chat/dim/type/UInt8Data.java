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
 *  Unsigned Char (8-bytes)
 */
public class UInt8Data extends Data implements IntegerData {

    public final int value;

    public static final UInt8Data ZERO = from(0);

    public UInt8Data(ByteArray data) {
        super(data);
        assert data.getSize() == 1 : "UInt8Data error: size=" + data.getSize();
        this.value = data.getByte(0) & 0xFF;
    }

    public UInt8Data(byte[] bytes, int offset) {
        super(bytes, offset, 1);
        assert bytes.length >= (offset + 1) : "UInt8Data error: offset=" + offset + ", length=" + bytes.length;
        this.value = bytes[offset] & 0xFF;
    }

    public UInt8Data(byte value) {
        super(new byte[1]);
        this.buffer[0] = value;
        this.value = value & 0xFF;
    }

    public UInt8Data(int value) {
        super(new byte[1]);
        this.buffer[0] = (byte) (value & 0xFF);
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

    public byte getByteValue() {
        return (byte) (value & 0xFF);
    }

    //
    //  Factories
    //

    public static UInt8Data from(UInt8Data data) {
        return data;
    }

    public static UInt8Data from(ByteArray data) {
        if (data.getSize() < 1) {
            return null;
        } else if (data.getSize() > 1) {
            data = data.slice(0, 1);
        }
        return new UInt8Data(data);
    }

    public static UInt8Data from(byte[] bytes) {
        if (bytes.length < 1) {
            return null;
        }
        return new UInt8Data(bytes, 0);
    }
    public static UInt8Data from(byte[] bytes, int offset) {
        if (bytes.length < (offset + 1)) {
            return null;
        }
        return new UInt8Data(bytes, offset);
    }

    public static UInt8Data from(byte value) {
        return new UInt8Data(value);
    }
    public static UInt8Data from(int value) {
        return new UInt8Data(value);
    }
}
