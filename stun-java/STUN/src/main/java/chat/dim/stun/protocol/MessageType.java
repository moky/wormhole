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
package chat.dim.stun.protocol;

import java.util.HashMap;
import java.util.Map;

import chat.dim.tlv.Data;
import chat.dim.tlv.UInt16Data;

/*  [RFC] https://www.ietf.org/rfc/rfc5389.txt
 *
 *                      0                 1
 *                      2  3  4 5 6 7 8 9 0 1 2 3 4 5
 *
 *                     +--+--+-+-+-+-+-+-+-+-+-+-+-+-+
 *                     |M |M |M|M|M|C|M|M|M|C|M|M|M|M|
 *                     |11|10|9|8|7|1|6|5|4|0|3|2|1|0|
 *                     +--+--+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *              Figure 3: Format of STUN Message Type Field
 */
public class MessageType extends UInt16Data {

    private final String name;

    public MessageType(MessageType type) {
        super(type);
        name = type.name;
        s_types.put(type.getIntValue(), this);
    }

    public MessageType(Data data, int value, String name) {
        super(data, value);
        this.name = name;
        s_types.put(value, this);
    }

    public MessageType(byte[] bytes, int value, String name) {
        super(bytes, value);
        this.name = name;
        s_types.put(value, this);
    }

    public MessageType(int value, String name) {
        this(bytesFromLong(value, 2), value, name);
    }

    @Override
    public String toString() {
        return name;
    }

    //
    //  Factory
    //

    public static synchronized MessageType getInstance(int value) {
        MessageType type = s_types.get(value);
        if (type == null) {
            //type = new MessageType(value, "MsgType-" + Integer.toHexString(value));
            throw new NullPointerException("msg type error: " + value);
        }
        return type;
    }

    public static MessageType parse(Data data) {
        if (data.length < 2 || (data.getByte(0) & 0xC0) != 0) {
            // format: 00xx xxxx, xxxx, xxxx
            return null;
        } else if (data.length > 2) {
            data = data.slice(0, 2);
        }
        int value = data.getUInt16Value(0);
        return getInstance(value);
    }

    private static final Map<Integer, MessageType> s_types = new HashMap<>();

    public static MessageType BindRequest = new MessageType(0x0001, "Bind Request");
    public static MessageType BindResponse = new MessageType(0x0101, "Bind Response");
    public static MessageType BindErrorResponse = new MessageType(0x0111, "Bind Error Response");
    public static MessageType SharedSecretRequest = new MessageType(0x0002, "Shared Secret Request");
    public static MessageType SharedSecretResponse = new MessageType(0x0102, "Shared Secret Response");
    public static MessageType SharedSecretErrorResponse = new MessageType(0x0112, "Shared Secret Error Response");
}
