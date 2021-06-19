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
        assert data.getLength() == 4 : "UInt32Data error: " + data.getLength();
        this.value = value;
    }

    public UInt32Data(ByteArray data, Endian endian) {
        super(data);
        assert data.getLength() == 4 : "UInt32Data error: " + data.getLength();
        this.value = IntegerData.getValue(data, 0, 4, endian);
    }

    public UInt32Data(byte[] bytes, long value) {
        super(bytes, 0, 4);
        this.value = value;
    }

    public UInt32Data(byte[] bytes, Endian endian) {
        super(bytes, 0, 4);
        this.value = IntegerData.getValue(bytes, 0, 4, endian);
    }

    public UInt32Data(byte[] bytes, int start, Endian endian) {
        super(bytes, start, 4);
        this.value = IntegerData.getValue(bytes, start, 4, endian);
    }

    @Override
    public int getIntValue() {
        return (int) value;
    }

    @Override
    public long getLongValue() {
        return value;
    }

    public static UInt32Data from(long value, Endian endian) {
        byte[] buffer = new byte[4];
        IntegerData.setValue(value, buffer, 0, 4, endian);
        return new UInt32Data(buffer, value);
    }
}
