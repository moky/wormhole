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
import chat.dim.type.UInt8Data;

/**
 *  Fixed Length (8 bits)
 *  ~~~~~~~~~~~~~~~~~~~~~
 */
public class Length8 extends UInt8Data implements Length {

    public static final Length8 ZERO = from(UInt8Data.ZERO);

    public Length8(ByteArray data) {
        super(data);
    }

    public Length8(byte value) {
        super(value);
    }

    public Length8(int value) {
        super(value);
    }

    //
    //  Factories
    //

    public static Length8 from(Length8 length) {
        return length;
    }

    public static Length8 from(UInt8Data data) {
        return new Length8(data);
    }

    public static Length8 from(ByteArray data) {
        if (data.getSize() < 1) {
            return null;
        } else if (data.getSize() > 1) {
            data = data.slice(0, 1);
        }
        return new Length8(data);
    }

    public static Length8 from(byte value) {
        return new Length8(value);
    }
    public static Length8 from(int value) {
        return new Length8(value);
    }
    public static Length8 from(Byte value) {
        return new Length8(value);
    }
    public static Length8 from(Integer value) {
        return new Length8(value);
    }

    // parse length with tag
    public static Length parse(ByteArray data, Tag tag) {
        return from(data);
    }
}
