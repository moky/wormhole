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

import chat.dim.tlv.Data;
import chat.dim.tlv.MutableData;
import chat.dim.tlv.Tag;

public class FieldName extends Tag {

    public final String name;

    public FieldName(FieldName type) {
        super(type);
        name = type.name;
    }

    public FieldName(Data data, String name) {
        super(data);
        this.name = name;
    }

    public FieldName(String name) {
        this(build(name), name);
    }

    private static Data build(String name) {
        byte[] bytes = name.getBytes(Charset.forName("UTF-8"));
        MutableData data = new MutableData(bytes.length + 1);
        data.append(bytes);
        data.append(0);  // add '\0' for tail
        return data;
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof FieldName) {
            return equals(((FieldName) other).name);
        }
        return super.equals(other);
    }
    public boolean equals(String other) {
        return name.equals(other);
    }

    @Override
    public int hashCode() {
        return name.hashCode();
    }

    @Override
    public String toString() {
        return name;
    }

    public static FieldName parse(Data data) {
        int pos = 0;
        int len = data.getLength();
        for (; pos < len; ++pos) {
            if (data.getByte(pos) == 0) {
                break;
            }
        }
        if (pos == 0 || pos == len) {
            return null;
        }
        ++pos;  // includes the tail '\0'
        if (pos < len) {
            data = data.slice(0, pos);
        }
        String name = data.toString().trim();
        return new FieldName(data, name);
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
