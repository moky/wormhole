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
 *  Unsigned Integer (32-bytes)
 */
public class UInt32Data extends IntegerData {

    public UInt32Data(UInt32Data data) {
        super(data);
    }

    public UInt32Data(Data data, long value) {
        super(data, value);
    }

    public UInt32Data(byte[] bytes, long value) {
        super(bytes, value);
    }

    public UInt32Data(long value) {
        super(bytesFromLong(value, 4), value);
    }

    //
    //  Factories
    //

    public static UInt32Data fromBytes(byte[] bytes) {
        return fromData(new Data(bytes, 0, 4));
    }

    public static UInt32Data fromData(Data data) {
        data = data.slice(0, 4);
        return new UInt32Data(data, data.getUInt32Value(0));
    }
}
