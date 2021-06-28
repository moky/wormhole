/* license: https://mit-license.org
 *
 *  STUN: Session Traversal Utilities for NAT
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
package chat.dim.stun.valus;

import java.nio.charset.Charset;

import chat.dim.tlv.Entry;
import chat.dim.tlv.StringValue;
import chat.dim.type.ByteArray;
import chat.dim.type.MutableData;

/**  15.10.  SOFTWARE
 *
 *    The SOFTWARE attribute contains a textual description of the software
 *    being used by the agent sending the message.  It is used by clients
 *    and servers.  Its value SHOULD include manufacturer and version
 *    number.  The attribute has no impact on operation of the protocol,
 *    and serves only as a tool for diagnostic and debugging purposes.  The
 *    value of SOFTWARE is variable length.  It MUST be a UTF-8 [RFC3629]
 *    encoded sequence of less than 128 characters (which can be as long as
 *    763 bytes).
 */
public class SoftwareValue extends StringValue {

    public SoftwareValue(ByteArray data, String description) {
        super(data, description);
    }

    //
    //  Factories
    //

    public static SoftwareValue from(SoftwareValue value) {
        return value;
    }

    public static SoftwareValue from(ByteArray data) {
        String string = new String(data.getBytes(), Charset.forName("UTF-8"));
        return new SoftwareValue(data, string.trim());
    }

    public static SoftwareValue from(String string) {
        return new SoftwareValue(getData(string), string);
    }

    // parse value with tag & length
    public static Entry.Value parse(ByteArray data, Entry.Tag tag, Entry.Length length) {
        return from(data);
    }

    private static ByteArray getData(String description) {
        byte[] bytes = description.getBytes(Charset.forName("UTF-8"));
        int length = bytes.length;
        int tail = length & 3;
        if (tail > 0) {
            length += 4 - tail;
        }
        MutableData data = new MutableData(length);
        data.append(bytes);
        if (tail > 0) {
            // set '\0' to fill the tail spaces
            data.setByte(length - 1, (byte) 0);
        }
        return data;
    }
}
