/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
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
package chat.dim.tlv;

/**
 *  Unsigned Char (8-bytes)
 */
public class UInt8Data extends IntegerData {

    public UInt8Data(UInt8Data data) {
        super(data);
    }

    public UInt8Data(Data data, int value) {
        super(data, value);
    }

    public UInt8Data(byte[] bytes, int value) {
        super(bytes, value);
    }

    public UInt8Data(Data data) {
        super(data, data.getByte(0));
    }

    public UInt8Data(byte[] bytes) {
        super(bytes, bytes[0]);
    }

    public UInt8Data(int value) {
        super(bytesFromLong(value, 1), value);
    }

    public byte getByteValue() {
        return (byte) (value & 0xFF);
    }

    //
    //  Factories
    //

    public static UInt8Data fromBytes(byte[] bytes) {
        return fromData(new Data(bytes, 0, 1));
    }

    public static UInt8Data fromData(Data data) {
        data = data.slice(0, 1);
        return new UInt8Data(data, data.getUInt8Value(0));
    }
}
