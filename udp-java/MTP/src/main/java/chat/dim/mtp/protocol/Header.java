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
package chat.dim.mtp.protocol;

import chat.dim.tlv.Data;
import chat.dim.tlv.MutableData;
import chat.dim.tlv.UInt32Data;

/*    Package Header:
 *
 *         0                   1                   2                   3
 *         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *        |      'D'      |      'I'      |      'M'      | H-Len |  Type |
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *        |                    Transaction ID (64 bits)
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *                             Transaction ID (64 bits)                   |
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *        |               Fragment Count (32 bits) OPTIONAL               |
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *        |               Fragment Index (32 bits) OPTIONAL               |
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *        |                 Body Length (32 bits) OPTIONAL                |
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *        ** Magic Code **:
 *            Always be 'DIM'
 *
 *        ** Header Length **:
 *            4 bits header length is the length of the header in 32 bit words.
 *            Note that the minimum value for a correct header is 3 (12 bytes).
 *
 *        ** Data Type **:
 *            Indicates what kind of the body data is.
 *
 *        ** Transaction ID **
 *            64 bits transaction ID is a random number for distinguishing
 *            different messages.
 *
 *        ** Count & Index **:
 *            If data type is a fragment message (or its respond),
 *            there is a field 'count' following the transaction ID,
 *            which indicates the message was split to how many fragments;
 *            and there is another field 'offset' following the 'count'.
 *
 *        ** Body Length **:
 *            Defined only for TCP stream.
 *            If transfer by UDP, no need to define the body's length.
 */
public class Header extends Data {

    public final DataType type;
    public final TransactionID sn;
    public final int pages;
    public final int offset;
    public final int bodyLength;

    /*  Max Length for message package body
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     *
     *  Each message package before split should not more than 1GB,
     *  so the max pages should not more than about 2,000,000.
     */
    public static int MAX_BODY_LENGTH = 1024 * 1024 * 1024; // 1GB
    public static int MAX_PAGES       = 1024 * 1024 * 2;    // 1GB

    public Header(Header head) {
        super(head);
        type = head.type;
        sn = head.sn;
        pages = head.pages;
        offset = head.offset;
        bodyLength = head.bodyLength;
    }

    /**
     *  Create package header
     *
     * @param data    - header data view
     * @param type    - package body data type
     * @param sn      - transaction ID
     * @param pages   - fragment count [OPTIONAL], default is 1
     * @param offset  - fragment index [OPTIONAL], default is 0
     * @param bodyLen - length of body [OPTIONAL], default is -1 (unlimited)
     */
    public Header(Data data, DataType type, TransactionID sn, int pages, int offset, int bodyLen) {
        super(data);
        this.type = type;
        this.sn = sn;
        this.pages = pages;
        this.offset = offset;
        this.bodyLength = bodyLen;
    }

    public Header(Data data, DataType type, TransactionID sn, int bodyLen) {
        this(data, type, sn, 1, 0, bodyLen);
    }

    public Header(Data data, DataType type, TransactionID sn) {
        this(data, type, sn, 1, 0, -1);
    }

    public static Header parse(Data data) {
        int length = data.getLength();
        if (length < 4) {
            //throw new ArrayIndexOutOfBoundsException("package error: " + Arrays.toString(data));
            return null;
        }
        if (data.getByte(0) != 'D' || data.getByte(1) != 'I' || data.getByte(2) != 'M') {
            //throw new IllegalArgumentException("not a DIM package: " + Arrays.toString(data));
            return null;
        }
        // get header length & data type
        byte ch = data.getByte(3);
        int headLen = (ch & 0xF0) >> 2; // in bytes
        TransactionID sn = null;
        int pages = 1;
        int offset = 0;
        int bodyLen = -1;
        if (headLen == 4) {
            // simple header
            sn = TransactionID.ZERO;
        } else if (headLen == 8) {
            // simple header with body length
            sn = TransactionID.ZERO;
            bodyLen = (int) data.getUInt32Value(4);
        } else if (headLen >= 12) {
            // command/message/fragment header
            sn = TransactionID.parse(data.slice(4));
            if (headLen == 16) {
                // command/message header with body length
                bodyLen = (int) data.getUInt32Value(12);
            } else if (headLen >= 20) {
                // fragment header
                pages = (int) data.getUInt32Value(12);
                offset = (int) data.getUInt32Value(16);
                if (headLen == 24) {
                    // fragment header with body length
                    bodyLen = (int) data.getUInt32Value(20);
                }
            }
        }
        if (sn == null) {
            //throw new NullPointerException("head length error: " + headLen);
            return null;
        }
        if (pages < 1 || pages > MAX_PAGES) {
            //throw new IllegalArgumentException("pages error: " + pages);
            return null;
        }
        if (offset < 0 || offset >= pages) {
            //throw new IllegalArgumentException("offset error: " + offset);
            return null;
        }
        if (bodyLen < -1 || bodyLen > MAX_BODY_LENGTH) {
            //throw new IllegalArgumentException("body length error: " + bodyLen);
            return null;
        }
        DataType type = DataType.getInstance(ch & 0x0F);
        return new Header(data.slice(0, headLen), type, sn, pages, offset, bodyLen);
    }

    //
    //  Factories
    //

    public static Header create(DataType type, TransactionID sn, int pages, int offset, int bodyLen) {
        int headLen = 4;  // in bytes
        // transaction ID
        assert sn != null : "transaction ID should not be null, use TransactionID.ZERO instead";
        if (!sn.equals(TransactionID.ZERO)) {
            headLen += 8;
        }
        Data options;
        // pages & offset
        assert type != null : "data type should not be null";
        if (type.equals(DataType.MessageFragment)) {
            // message fragment (or its respond)
            assert pages > 1 && pages > offset : "pages error: " + pages + ", " + offset;
            Data d1 = new UInt32Data(pages);
            Data d2 = new UInt32Data(offset);
            options = d1.concat(d2);
            headLen += 8;
        } else {
            // command message (or its respond)
            assert pages == 1 && offset == 0 : "pages error: " + pages + ", " + offset;
            options = null;
        }
        // body length
        if (bodyLen >= 0) {
            Data d3 = new UInt32Data(bodyLen);
            if (options == null) {
                options = d3;
            } else {
                options = options.concat(d3);
            }
            headLen += 4;
        }
        // generate header data
        MutableData data = new MutableData(headLen);
        data.append('D').append('I').append('M');
        data.append((headLen << 2) | (type.value & 0x0F));
        if (!sn.equals(TransactionID.ZERO)) {
            data.append(sn);
        }
        if (options != null) {
            data.append(options);
        }
        return new Header(data, type, sn, pages, offset, bodyLen);
    }

    //
    //  UDP
    //

    public static Header create(DataType type, TransactionID sn, int pages, int offset) {
        return create(type, sn, pages, offset, -1);
    }

    public static Header create(DataType type, int pages, int offset) {
        return create(type, TransactionID.generate(), pages, offset, -1);
    }

    public static Header create(DataType type, TransactionID sn) {
        return create(type, sn, 1, 0, -1);
    }

    public static Header create(DataType type) {
        return create(type, TransactionID.generate(), 1, 0, -1);
    }

    //
    //  TCP
    //

    public static Header create(DataType type, TransactionID sn, int bodyLen) {
        return create(type, sn, 1, 0, bodyLen);
    }

    public static Header create(DataType type, int bodyLen) {
        return create(type, TransactionID.generate(), 1, 0, bodyLen);
    }
}
