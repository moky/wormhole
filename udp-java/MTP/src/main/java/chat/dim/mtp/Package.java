/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
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
package chat.dim.mtp;

import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class Package extends Data {

    public final Header head;
    public final ByteArray body;

    public Package(ByteArray data, Header wrapper, ByteArray payload) {
        super(data);
        head = wrapper;
        body = payload;
    }

    public boolean isResponse() {
        return head.type.isResponse();
    }
    public boolean isFragment() {
        return head.type.isFragment();
    }
    public boolean isCommand() {
        return head.type.isCommand();
    }
    public boolean isCommandResponse() {
        return head.type.isCommandResponse();
    }
    public boolean isMessage() {
        return head.type.isMessage();
    }
    public boolean isMessageResponse() {
        return head.type.isMessageResponse();
    }
    public boolean isMessageFragment() {
        return head.type.isMessageFragment();
    }

    int getFragmentIndex() {
        return head.index;
    }

    public static Package parse(ByteArray data) {
        // get package head
        final Header head = Header.parse(data);
        if (head == null) {
            //throw new NullPointerException("package head error: " + Arrays.toString(data));
            return null;
        }
        // check lengths
        int headLen = head.getSize();
        int bodyLen = head.bodyLength;
        if (bodyLen < 0) {
            // UDP (unlimited)
            assert bodyLen == -1 : "body length error: " + bodyLen;
        } else {
            // TCP
            int packLen = headLen + bodyLen;
            int dataLen = data.getSize();
            if (dataLen < packLen) {
                //throw new ArrayIndexOutOfBoundsException("package length error: " + Arrays.toString(data));
                return null;
            } else if (dataLen > packLen) {
                data = data.slice(0, packLen);
            }
        }
        return new Package(data, head, data.slice(headLen));
    }

    //
    //  Factory
    //

    public static Package create(DataType type, TransactionID sn, int pages, int index, int bodyLen, ByteArray body) {
        assert body != null : "package body should not be null";
        // create package with header
        Header head = Header.create(type, sn, pages, index, bodyLen);
        ByteArray data;
        if (body.getSize() > 0) {
            data = head.concat(body);
        } else {
            data = head;
        }
        return new Package(data, head, body);
    }
}
