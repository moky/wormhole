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
import chat.dim.type.Data;
import chat.dim.type.IntegerData;
import chat.dim.type.VarIntData;

/**
 *  Variable Tag
 *  ~~~~~~~~~~~~
 *
 *  A tag that starts with a variable integer indicating its content length
 *
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |     Length    |               Content (variable)              |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */
public class VarTag extends Data implements Triad.Tag {

    public final IntegerData length;
    public final ByteArray content;

    public VarTag(ByteArray data, IntegerData length, ByteArray content) {
        super(data);
        this.length = length;
        this.content = content;
        assert content != null : "Variable Tag error";
        assert data.getLength() == (length.getLength() + content.getLength()) : "VarTag error: " + data.getLength();
    }

    protected static IntegerData getLength(ByteArray data) {
        return VarIntData.from(data);
    }
    protected static ByteArray getContent(ByteArray data, IntegerData length) {
        int offset = length.getLength();
        int size = length.getIntValue();
        if ((offset + size) > data.getLength()) {
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
        int size = length.getLength() + content.getLength();
        if (size < data.getLength()) {
            data = data.slice(0, size);
        }
        return new VarTag(data, length, content);
    }
    public static VarTag from(IntegerData length, ByteArray content) {
        if (length == null) {
            length = VarIntData.from(content.getLength());
        } else {
            assert length.getIntValue() == content.getLength() :
                    "VarTag error: " + length.getIntValue() + ", " + content.getLength();
        }
        ByteArray data = length.concat(content);
        return new VarTag(data, length, content);
    }
}
