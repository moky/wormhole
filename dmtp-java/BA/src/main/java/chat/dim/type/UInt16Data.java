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
        assert data.getLength() == 2 : "UInt16Data error: " + data.getLength();
        this.value = value;
    }

    public UInt16Data(ByteArray data, Endian endian) {
        super(data);
        assert data.getLength() == 2 : "UInt16Data error: " + data.getLength();
        this.value = (int) IntegerData.getValue(data, endian);
    }

    public UInt16Data(byte[] bytes, int value) {
        super(bytes, 0, 2);
        this.value = value;
    }

    public UInt16Data(byte[] bytes, Endian endian) {
        super(bytes, 0, 2);
        this.value = (int) IntegerData.getValue(bytes, 0, 2, endian);
    }

    public UInt16Data(byte[] bytes, int start, Endian endian) {
        super(bytes, start, 2);
        this.value = (int) IntegerData.getValue(bytes, start, 2, endian);
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof IntegerData) {
            return value == ((IntegerData) other).getIntValue();
        } else if (other instanceof ByteArray) {
            return equals((ByteArray) other);
        } else {
            return false;
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

    public static UInt16Data from(int value, Endian endian) {
        byte[] buffer = new byte[2];
        IntegerData.setValue(value, buffer, 0, 2, endian);
        return new UInt16Data(buffer, value);
    }
}
