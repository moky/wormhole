/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
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
package chat.dim.dmtp.fields;

import java.nio.charset.Charset;

import chat.dim.tlv.Tag;

public class FieldName extends Tag {

    public final String name;

    public FieldName(byte[] data, String name) {
        super(data);
        this.name = name;
    }

    public FieldName(String name) {
        this(build(name), name);
    }

    private static byte[] build(String name) {
        byte[] data = name.getBytes(Charset.forName("UTF-8"));
        int len = data.length;
        byte[] buffer = new byte[len + 1];  // append '\0' to tail
        System.arraycopy(data, 0, buffer, 0, len);
        return buffer;
    }

    public boolean equals(String other) {
        return name.equals(other);
    }

    @Override
    public String toString() {
        return name;
    }

    public static FieldName parse(byte[] data) {
        int pos = 0;
        int len = data.length;
        for (; pos < len; ++pos) {
            if (data[pos] == 0) {
                break;
            }
        }
        if (pos == 0 || pos == len) {
            return null;
        }
        ++pos;  // includes the tail '\0'
        if (pos < len) {
            data = slice(data, 0, pos);
        }
        String name = new String(data, 0, pos-1, Charset.forName("UTF-8"));
        return new FieldName(data, name);
    }
}
