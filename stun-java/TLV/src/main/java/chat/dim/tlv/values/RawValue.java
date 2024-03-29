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
package chat.dim.tlv.values;

import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.tlv.Value;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

/*
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |         Type                  |            Length             |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Value (variable)                ....
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

public class RawValue extends Data implements Value {

    public static final RawValue ZERO = from(Data.ZERO);

    public RawValue(ByteArray data) {
        super(data);
    }

    public RawValue(byte[] bytes, int offset, int size) {
        super(bytes, offset, size);
    }

    public RawValue(byte[] bytes) {
        super(bytes, 0, bytes.length);
    }

    //
    //  Factories
    //

    public static RawValue from(RawValue value) {
        return value;
    }

    public static RawValue from(ByteArray data) {
        return new RawValue(data);
    }

    public static RawValue from(byte[] bytes) {
        return new RawValue(bytes);
    }

    public static RawValue from(byte[] bytes, int offset, int size) {
        return new RawValue(bytes, offset, size);
    }

    // parse value with tag & length
    public static Value parse(ByteArray data, Tag tag, Length length) {
        return from(data);
    }
}
