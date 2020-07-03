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
    public final Data body;

    public Package(Package pack) {
        super(pack);
        head = pack.head;
        body = pack.body;
    }

    public Package(Data data, Header head, Data body) {
        super(data);
        this.head = head;
        this.body = body;
    }

    public Package(Header head, Data body) {
        this(head.concat(body), head, body);
    }

    public Package(Header head) {
        this(head, head, Data.ZERO);
    }

    //
    //  Factories
    //

    public static Package create(MessageType type, TransactionID sn, Data body) {
        if (sn == null) {
            sn = new TransactionID();
        }
        if (body == null) {
            body = Data.ZERO;
        }
        MessageLength len = new MessageLength(body.getLength());
        Header head = new Header(type, len, sn);
        Data data = head.concat(body);
        return new Package(data, head, body);
    }

    public static Package parse(Data data) {
        // get STUN head
        Header head = Header.parse(data);
        if (head == null) {
            // not a STUN message?
            return null;
        }
        // check message length
        int packLen = head.getLength() + head.msgLength.getIntValue();
        int dataLen = data.getLength();
        if (dataLen < packLen) {
            //throw new IndexOutOfBoundsException("STUN package length error: " + dataLen + ", " + packLen);
            return null;
        } else if (dataLen > packLen) {
            data = data.slice(0, packLen);
        }
        // get attributes body
        Data body = data.slice(head.getLength());
        return new Package(data, head, body);
    }

    // const body
    public static final byte[] OK = {'O', 'K'};
    public static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
