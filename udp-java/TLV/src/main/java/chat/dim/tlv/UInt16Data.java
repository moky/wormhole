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
 *  Unsigned Short Integer (16-bytes)
 */
public class UInt16Data extends IntegerData {

    public UInt16Data(UInt16Data data) {
        super(data);
    }

    public UInt16Data(Data data, int value) {
        super(data, value);
    }

    public UInt16Data(byte[] bytes, int value) {
        super(bytes, value);
    }

    public UInt16Data(int value) {
        super(bytesFromLong(value, 2), value);
    }

    //
    //  Factories
    //

    public static UInt16Data fromBytes(byte[] bytes) {
        return fromData(new Data(bytes, 0, 2));
    }

    public static UInt16Data fromData(Data data) {
        data = data.slice(0, 2);
        return new UInt16Data(data, data.getUInt16Value(0));
    }
}
