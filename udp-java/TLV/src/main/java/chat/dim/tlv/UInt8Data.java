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

    public UInt8Data(Data data, int value) {
        super(data, value);
    }

    public UInt8Data(UInt8Data data) {
        super(data, data.value);
    }

    public UInt8Data(int value) {
        super(IntegerData.fromInt(value, 1), value);
    }

    public UInt8Data(byte value) {
        this(value & 0xFF);
    }

    //
    //  Factories
    //

    public static UInt8Data fromBytes(byte[] bytes) {
        return fromData(new Data(bytes, 0, 1));
    }

    public static UInt8Data fromData(Data other) {
        if (other instanceof UInt8Data) {
            //return new UInt8Data(other, (int) ((UInt8Data) other).value);
            return (UInt8Data) other;
        }
        other = other.slice(0, 1);
        IntegerData data = IntegerData.fromData(other);
        return new UInt8Data(other, (int) data.value);
    }
}
