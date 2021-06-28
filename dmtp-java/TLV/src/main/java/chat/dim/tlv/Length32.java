/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
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

import chat.dim.network.DataConvert;
import chat.dim.type.ByteArray;
import chat.dim.type.UInt32Data;

/**
 *  Fixed Length (32 bits)
 *  ~~~~~~~~~~~~~~~~~~~~~~
 */
public class Length32 extends UInt32Data implements Entry.Length {

    public static final Length32 ZERO = from(UInt32Data.ZERO);

    public Length32(UInt32Data data) {
        super(data, data.value, data.endian);
    }

    public Length32(ByteArray data, long value, Endian endian) {
        super(data, value, endian);
    }

    //
    //  Factories
    //

    public static Length32 from(Length32 length) {
        return length;
    }

    public static Length32 from(UInt32Data data) {
        return new Length32(data, data.value, data.endian);
    }

    public static Length32 from(ByteArray data) {
        if (data.getSize() < 4) {
            return null;
        } else if (data.getSize() > 4) {
            data = data.slice(0, 4);
        }
        return new Length32(DataConvert.getUInt32Data(data));
    }

    public static Length32 from(int value) {
        return new Length32(DataConvert.getUInt32Data(value));
    }

    // parse length with tag
    public static Entry.Length parse(ByteArray data, Entry.Tag tag) {
        return from(data);
    }
}
