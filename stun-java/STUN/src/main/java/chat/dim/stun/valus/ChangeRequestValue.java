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

import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.tlv.Value;
import chat.dim.tlv.values.Value32;
import chat.dim.type.ByteArray;
import chat.dim.type.IntegerData;
import chat.dim.type.UInt32Data;

/*  Rosenberg, et al.           Standards Track                    [Page 27]
 *
 *  RFC 3489                          STUN                        March 2003
 *
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

/**  11.2.4 CHANGE-REQUEST
 *
 *       The CHANGE-REQUEST attribute is used by the client to request that
 *       the server use a different address and/or port when sending the
 *       response.  The attribute is 32 bits long, although only two bits (A
 *       and B) are used:
 */
public class ChangeRequestValue extends Value32 {

    private final String name;

    public ChangeRequestValue(UInt32Data data, String name) {
        super(data);
        this.name = name;
    }

    @Override
    public String toString() {
        return name;
    }

    //
    //  Factories
    //

    public static ChangeRequestValue from(ChangeRequestValue value) {
        return value;
    }

    public static ChangeRequestValue from(UInt32Data data) {
        return get(data.getIntValue());
    }

    public static ChangeRequestValue from(ByteArray data) {
        if (data.getSize() < 4) {
            return null;
        }
        return get(IntegerData.getInt32Value(data));
    }

    public static ChangeRequestValue from(int value) {
        return get(value);
    }

    public static synchronized ChangeRequestValue get(int value) {
        ChangeRequestValue crv = s_values.get(value);
        if (crv == null) {
            crv = create(value, "ChangeRequestValue-"+value);
        }
        return crv;
    }

    // parse value with tag & length
    public static Value parse(ByteArray data, Tag tag, Length length) {
        return from(data);
    }

    private static ChangeRequestValue create(int value, String name) {
        UInt32Data data = IntegerData.getUInt32Data(value);
        ChangeRequestValue crv = new ChangeRequestValue(data, name);
        s_values.put(value, crv);
        return crv;
    }

    private static final Map<Integer, ChangeRequestValue> s_values = new HashMap<>();

    public static final ChangeRequestValue ChangeIP        = create(0x00000004, "ChangeIP");
    public static final ChangeRequestValue ChangePort      = create(0x00000002, "ChangePort");
    public static final ChangeRequestValue ChangeIPAndPort = create(0x00000006, "ChangeIPAndPort");
}
