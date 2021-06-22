/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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

import java.nio.charset.Charset;

import chat.dim.type.ByteArray;
import chat.dim.type.Data;
import chat.dim.type.IntegerData;
import chat.dim.type.VarIntData;

public class StringTag extends VarTag {

    public final String string;

    public StringTag(VarTag tag, String string) {
        super(tag, tag.length, tag.content);
        this.string = string;
    }

    public StringTag(ByteArray data, IntegerData length, ByteArray content, String string) {
        super(data, length, content);
        this.string = string;
    }

    @Override
    public String toString() {
        return string;
    }

    //
    //  Factories
    //

    public static StringTag from(StringTag tag) {
        return tag;
    }

    public static StringTag from(VarTag tag) {
        return new StringTag(tag, getString(tag.content));
    }

    public static StringTag from(ByteArray data) {
        VarTag tag = VarTag.from(data);
        return tag == null ? null : new StringTag(tag, getString(tag.content));
    }

    public static StringTag from(String name) {
        ByteArray content = getContent(name);
        IntegerData length = VarIntData.from(content.getSize());
        ByteArray data = length.concat(content);
        return new StringTag(data, length, content, name);
    }

    // parse tag
    public static Triad.Tag parse(ByteArray data) {
        return from(data);
    }

    //
    //  Converting
    //

    private static String getString(ByteArray content) {
        return new String(content.getBytes(), Charset.forName("UTF-8"));
    }
    private static ByteArray getContent(String name) {
        return new Data(name.getBytes(Charset.forName("UTF-8")));
    }
}
