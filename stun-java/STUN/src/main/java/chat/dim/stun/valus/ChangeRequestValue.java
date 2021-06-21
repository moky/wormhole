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

import java.util.HashMap;
import java.util.Map;

import chat.dim.network.DataConvert;
import chat.dim.stun.attributes.AttributeLength;
import chat.dim.stun.attributes.AttributeType;
import chat.dim.stun.attributes.AttributeValue;
import chat.dim.type.ByteArray;

/*  11.2.4 CHANGE-REQUEST
 *
 *       The CHANGE-REQUEST attribute is used by the client to request that
 *       the server use a different address and/or port when sending the
 *       response.  The attribute is 32 bits long, although only two bits (A
 *       and B) are used:
 *
 *        0                   1                   2                   3
 *        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *       |0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 A B 0|
 *       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *       The meaning of the flags is:
 *
 *       A: This is the "change IP" flag.  If true, it requests the server
 *          to send the Binding Response with a different IP address than the
 *          one the Binding Request was received on.
 *
 *       B: This is the "change port" flag.  If true, it requests the
 *          server to send the Binding Response with a different port than the
 *          one the Binding Request was received on.
 *
 *    (Defined in RFC-3489, removed from RFC-5389)
 */

public class ChangeRequestValue extends AttributeValue {

    public final int value;
    private final String name;

    public ChangeRequestValue(ChangeRequestValue requestValue) {
        super(requestValue);
        value = requestValue.value;
        name = requestValue.name;
    }

    public ChangeRequestValue(ByteArray data, int value, String name) {
        super(data);
        this.value = value;
        this.name = name;
        s_values.put(value, this);
    }

    public ChangeRequestValue(int value, String name) {
        this(DataConvert.getUInt32Data(value), value, name);
    }

    public ChangeRequestValue(int value) {
        this(value, "ChangeRequestValue-"+value);
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (other instanceof ChangeRequestValue) {
            return equals(((ChangeRequestValue) other).value);
        }
        return false;
    }
    public boolean equals(int other) {
        return value == other;
    }

    @Override
    public int hashCode() {
        return Integer.hashCode(value);
    }

    @Override
    public String toString() {
        return name;
    }

    public static ChangeRequestValue parse(ByteArray data, AttributeType type, AttributeLength length) {
        return getInstance(data);
    }

    public static synchronized ChangeRequestValue getInstance(ByteArray data) {
        assert data.getLength() == 4 : "data length error";
        int value = DataConvert.getInt32Value(data);
        return getInstance(value);
    }
    public static synchronized ChangeRequestValue getInstance(int value) {
        ChangeRequestValue type = s_values.get(value);
        if (type == null) {
            type = new ChangeRequestValue(value);
        }
        return type;
    }

    private static final Map<Integer, ChangeRequestValue> s_values = new HashMap<>();

    public static ChangeRequestValue ChangeIP = new ChangeRequestValue(0x00000004, "ChangeIP");
    public static ChangeRequestValue ChangePort = new ChangeRequestValue(0x00000002, "ChangePort");
    public static ChangeRequestValue ChangeIPAndPort = new ChangeRequestValue(0x00000006, "ChangeIPAndPort");
}
