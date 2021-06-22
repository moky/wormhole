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

public class Package extends Data {

    public final Header head;
    public final ByteArray body;

    public Package(ByteArray data, Header head, ByteArray body) {
        super(data);
        this.head = head;
        this.body = body;
    }

    //
    //  Factories
    //

    public static Package create(MessageType type, TransactionID sn, ByteArray body) {
        MessageLength length;
        if (body == null) {
            body = Data.ZERO;
            length = MessageLength.ZERO;
        } else {
            length = MessageLength.from(body.getSize());
        }
        Header head;
        if (sn == null) {
            head = Header.create(type, length);
        } else {
            head = Header.create(type, length, sn);
        }
        ByteArray data = head.concat(body);
        return new Package(data, head, body);
    }

    public static Package parse(ByteArray data) {
        // get STUN head
        Header head = Header.parse(data);
        if (head == null) {
            // not a STUN message?
            return null;
        }
        // check message length
        int packLen = head.getSize() + head.msgLength.getIntValue();
        int dataLen = data.getSize();
        if (dataLen < packLen) {
            //throw new IndexOutOfBoundsException("STUN package length error: " + dataLen + ", " + packLen);
            return null;
        } else if (dataLen > packLen) {
            data = data.slice(0, packLen);
        }
        // get attributes body
        ByteArray body = data.slice(head.getSize());
        return new Package(data, head, body);
    }
}
