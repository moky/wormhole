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

import chat.dim.type.ByteArray;
import chat.dim.type.UInt8Data;

/**
 *  Fixed Char Tag (8 bits)
 *  ~~~~~~~~~~~~~~~~~~~~~~~
 */
public class Tag8 extends UInt8Data implements Entry.Tag {

    public static final Tag8 ZERO = from(UInt8Data.ZERO);

    public Tag8(ByteArray data) {
        super(data);
    }

    public Tag8(byte value) {
        super(value);
    }

    public Tag8(int value) {
        super(value);
    }

    //
    //  Factories
    //

    public static Tag8 from(Tag8 tag) {
        return tag;
    }

    public static Tag8 from(UInt8Data data) {
        return new Tag8(data);
    }

    public static Tag8 from(ByteArray data) {
        if (data.getSize() < 1) {
            return null;
        } else if (data.getSize() > 1) {
            data = data.slice(0, 1);
        }
        return new Tag8(data);
    }

    public static Tag8 from(byte value) {
        return new Tag8(value);
    }
    public static Tag8 from(int value) {
        return new Tag8(value);
    }

    // parse tag
    public static Entry.Tag parse(ByteArray data) {
        return from(data);
    }
}
