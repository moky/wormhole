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

import chat.dim.tlv.Data;

public class Package extends Data {

    public final Header head;
    public final byte[] body;

    public Package(byte[] data, Header head, byte[] body) {
        super(data);
        this.head = head;
        this.body = body;
    }

    public static Package parse(byte[] data) {
        // get STUN head
        Header head = Header.parse(data);
        if (head == null) {
            // not a STUN message?
            return null;
        }
        // check message length
        int packLen = (int) (head.length + head.msgLength.value);
        int dataLen = data.length;
        if (dataLen < packLen) {
            //throw new IndexOutOfBoundsException("STUN package length error: " + dataLen + ", " + packLen);
            return null;
        } else if (dataLen > packLen) {
            data = slice(data, 0, packLen);
        }
        // get attributes body
        byte[] body = slice(data, head.length);
        return new Package(data, head, body);
    }

    public static Package create(MessageType type, TransactionID sn, byte[] body) {
        MessageLength len = new MessageLength(body.length);
        Header head = Header.create(type, len, sn);
        byte[] data = concat(head.data, body);
        return new Package(data, head, body);
    }

    public static Package create(MessageType type, byte[] body) {
        TransactionID sn = TransactionID.create();
        return create(type, sn, body);
    }

    public static Package create(MessageType type, TransactionID sn) {
        byte[] body = new byte[0];
        return create(type, sn, body);
    }

    public static Package create(MessageType type) {
        TransactionID sn = TransactionID.create();
        byte[] body = new byte[0];
        return create(type, sn, body);
    }

    // const body
    public static final byte[] OK = {'O', 'K'};
    public static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
