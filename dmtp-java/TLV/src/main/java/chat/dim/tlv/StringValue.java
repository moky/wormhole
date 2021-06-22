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

import java.nio.charset.Charset;

import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class StringValue extends Data implements Triad.Value {

    public static final StringValue ZERO = from(Data.ZERO);

    public final String string;

    public StringValue(ByteArray data, String string) {
        super(data);
        this.string = string;
    }

    public StringValue(byte[] buffer, int offset, int size, String string) {
        super(buffer, offset, size);
        this.string = string;
    }

    public StringValue(byte[] bytes, String string) {
        super(bytes);
        this.string = string;
    }

    //
    //  Factories
    //

    public static StringValue from(StringValue value) {
        return value;
    }

    public static StringValue from(ByteArray data) {
        String string = new String(data.getBytes(), Charset.forName("UTF-8"));
        return new StringValue(data, string);
    }

    public static StringValue from(String string) {
        byte[] bytes = string.getBytes(Charset.forName("UTF-8"));
        return new StringValue(bytes, 0, bytes.length, string);
    }

    public static StringValue from(byte[] bytes) {
        String string = new String(bytes, Charset.forName("UTF-8"));
        return new StringValue(bytes, 0, bytes.length, string);
    }

    // parse value with tag & length
    public static Triad.Value parse(ByteArray data, Triad.Tag tag, Triad.Length length) {
        return from(data);
    }
}
