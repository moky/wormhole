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

import chat.dim.type.ByteArray;
import chat.dim.type.Data;
import chat.dim.type.MutableData;

/*  [RFC] https://www.ietf.org/rfc/rfc5389.txt
 *
 *    STUN Message Structure
 *    ~~~~~~~~~~~~~~~~~~~~~~
 *
 *   STUN messages are encoded in binary using network-oriented format
 *   (most significant byte or octet first, also commonly known as big-
 *   endian).  The transmission order is described in detail in Appendix B
 *   of RFC 791 [RFC0791].  Unless otherwise noted, numeric constants are
 *   in decimal (base 10).
 *
 *   All STUN messages MUST start with a 20-byte header followed by zero
 *   or more Attributes.  The STUN header contains a STUN message type,
 *   magic cookie, transaction ID, and message length.
 *
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |0 0|     STUN Message Type     |         Message Length        |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Magic Cookie                          |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *                            Transaction ID (96 bits)
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *                                                                      |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *                  Figure 2: Format of STUN Message Header
 *
 *   The message length MUST contain the size, in bytes, of the message
 *   not including the 20-byte STUN header.  Since all STUN attributes are
 *   padded to a multiple of 4 bytes, the last 2 bits of this field are
 *   always zero.  This provides another way to distinguish STUN packets
 *   from packets of other protocols.
 */
public class Header extends Data {

    public final MessageType type;
    public final MessageLength msgLength;
    public final TransactionID sn;

    public Header(ByteArray data, MessageType type, MessageLength length, TransactionID sn) {
        super(data);
        this.type = type;
        this.msgLength = length;
        this.sn = sn;
    }

    //
    //  Factories
    //

    public static Header create(MessageType type, MessageLength length) {
        return create(type, length, new TransactionID());
    }

    public static Header create(MessageType type, MessageLength length, TransactionID sn) {
        MutableData data = new MutableData(type.getLength() + length.getLength() + sn.getLength());
        data.append(type);
        data.append(length);
        data.append(sn);
        return new Header(data, type, length, sn);
    }

    public static Header parse(ByteArray data) {
        int pos;
        // get message type
        MessageType type = MessageType.parse(data);
        if (type == null) {
            return null;
        }
        pos = type.getLength();
        // get message length
        MessageLength len = MessageLength.parse(data.slice(pos));
        if (len == null) {
            return null;
        }
        pos += len.getLength();
        // get transaction ID
        TransactionID sn = TransactionID.parse(data.slice(pos));
        if (sn == null) {
            return null;
        }
        pos += sn.getLength();
        assert pos == 20 : "header length error: " + pos;
        if (data.getLength() > pos) {
            data = data.slice(0, pos);
        }
        // create
        return new Header(data, type, len, sn);
    }
}
