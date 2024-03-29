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
package chat.dim.tlv.lengths;

import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.type.ByteArray;
import chat.dim.type.IntegerData;
import chat.dim.type.UInt16Data;

/*
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |             Type              |            Length             |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Value (variable)                ....
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

/**
 *  Fixed Length (16 bits)
 *  ~~~~~~~~~~~~~~~~~~~~~~
 */
public class Length16 extends UInt16Data implements Length {

    public static final Length16 ZERO = from(UInt16Data.ZERO);

    public Length16(UInt16Data data) {
        super(data, data.value, data.endian);
    }

    public Length16(ByteArray data, int value, Endian endian) {
        super(data, value, endian);
    }

    //
    //  Factories
    //

    public static Length16 from(Length16 length) {
        return length;
    }

    public static Length16 from(UInt16Data data) {
        return new Length16(data, data.value, data.endian);
    }

    public static Length16 from(ByteArray data) {
        if (data.getSize() < 2) {
            return null;
        } else if (data.getSize() > 2) {
            data = data.slice(0, 2);
        }
        return new Length16(IntegerData.getUInt16Data(data));
    }

    public static Length16 from(int value) {
        return new Length16(IntegerData.getUInt16Data(value));
    }
    public static Length16 from(Integer value) {
        return new Length16(IntegerData.getUInt16Data(value));
    }

    // parse length with tag
    public static Length parse(ByteArray data, Tag tag) {
        return from(data);
    }
}
