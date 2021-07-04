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
package chat.dim.tlv.tags;

import chat.dim.network.DataConvert;
import chat.dim.tlv.Tag;
import chat.dim.type.ByteArray;
import chat.dim.type.UInt32Data;

/**
 *  Fixed Tag (32 bits)
 *  ~~~~~~~~~~~~~~~~~~~
 */
public class Tag32 extends UInt32Data implements Tag {

    public static final Tag32 ZERO = from(UInt32Data.ZERO);

    public Tag32(UInt32Data data) {
        super(data, data.value, data.endian);
    }

    public Tag32(ByteArray data, long value, Endian endian) {
        super(data, value, endian);
    }

    //
    //  Factories
    //

    public static Tag32 from(Tag32 tag) {
        return tag;
    }

    public static Tag32 from(UInt32Data data) {
        return new Tag32(data, data.value, data.endian);
    }

    public static Tag32 from(ByteArray data) {
        if (data.getSize() < 4) {
            return null;
        } else if (data.getSize() > 4) {
            data = data.slice(0, 4);
        }
        return new Tag32(DataConvert.getUInt32Data(data));
    }

    public static Tag32 from(int value) {
        return new Tag32(DataConvert.getUInt32Data(value));
    }

    // parse tag
    public static Tag parse(ByteArray data) {
        return from(data);
    }
}
