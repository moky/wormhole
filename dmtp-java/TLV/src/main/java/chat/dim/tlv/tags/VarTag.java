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

import chat.dim.tlv.Tag;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;
import chat.dim.type.IntegerData;
import chat.dim.type.VarIntData;

/*
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |     Length    |               Content (variable)              |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

/**
 *  Variable Tag
 *  ~~~~~~~~~~~~
 *
 *  A tag that starts with a variable integer indicating its content length
 */
public class VarTag extends Data implements Tag {

    public static final VarTag ZERO = from(VarIntData.ZERO, Data.ZERO);

    public final IntegerData length;
    public final ByteArray content;

    public VarTag(ByteArray data, IntegerData length, ByteArray content) {
        super(data);
        this.length = length;
        this.content = content;
        assert content != null : "Variable Tag error";
        assert data.getSize() == (length.getSize() + content.getSize()) : "VarTag error: " + data.getSize();
    }

    private static IntegerData getLength(ByteArray data) {
        return VarIntData.from(data);
    }
    private static ByteArray getContent(ByteArray data, IntegerData length) {
        int offset = length.getSize();
        int size = length.getIntValue();
        if ((offset + size) > data.getSize()) {
            return null;
        }
        return data.slice(offset, offset + size);
    }

    //
    //  Factories
    //

    public static VarTag from(VarTag tag) {
        return tag;
    }

    public static VarTag from(ByteArray data) {
        IntegerData length = getLength(data);
        if (length == null) {
            return null;
        }
        ByteArray content = getContent(data, length);
        if (content == null) {
            return null;
        }
        int size = length.getSize() + content.getSize();
        if (size < data.getSize()) {
            data = data.slice(0, size);
        }
        return new VarTag(data, length, content);
    }
    public static VarTag from(IntegerData length, ByteArray content) {
        if (length == null) {
            length = VarIntData.from(content.getSize());
        } else {
            assert length.getIntValue() == content.getSize() :
                    "VarTag error: " + length.getIntValue() + ", " + content.getSize();
        }
        ByteArray data = length.concat(content);
        return new VarTag(data, length, content);
    }

    // parse tag
    public static Tag parse(ByteArray data) {
        return from(data);
    }
}
