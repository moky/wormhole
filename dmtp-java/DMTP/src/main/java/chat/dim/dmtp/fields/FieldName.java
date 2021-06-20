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

import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;
import chat.dim.type.MutableData;

public class FieldName extends Data implements Triad.Tag {

    public final String name;

    public FieldName(ByteArray data, String name) {
        super(data);
        this.name = name;
    }

    public FieldName(ByteArray data) {
        this(data, getString(data));
    }

    public FieldName(String name) {
        this(getData(name), name);
    }

    private static String getString(ByteArray data) {
        int tail = data.getLength() - 1;
        assert data.getByte(tail) == '\0' : "data error: " + data;
        data = data.slice(0, tail);
        return new String(data.getBytes(), Charset.forName("UTF-8"));
    }
    private static Data getData(String name) {
        byte[] bytes = name.getBytes(Charset.forName("UTF-8"));
        MutableData data = new MutableData(bytes.length + 1);
        data.append(bytes);
        data.append((byte) 0);
        return data;
    }

    @Override
    public String toString() {
        return name;
    }

    //
    //  Field names
    //

    public static final FieldName ID              = new FieldName("ID");       // user ID
    public static final FieldName SOURCE_ADDRESS  = new FieldName("SOURCE-ADDRESS");
    public static final FieldName MAPPED_ADDRESS  = new FieldName("MAPPED-ADDRESS");
    public static final FieldName RELAYED_ADDRESS = new FieldName("RELAYED-ADDRESS");
    public static final FieldName TIME            = new FieldName("TIME");   // timestamp (uint32) stored in network order (big endian)
    public static final FieldName SIGNATURE       = new FieldName("SIGNATURE");
    public static final FieldName NAT             = new FieldName("NAT");     // NAT type
}
