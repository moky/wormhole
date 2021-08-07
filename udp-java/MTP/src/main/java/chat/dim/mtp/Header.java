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
import chat.dim.type.IntegerData;
import chat.dim.type.MutableData;

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

    public static final byte[] MAGIC_CODE = {'D', 'I', 'M'};

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
    public Header(ByteArray data, DataType type, TransactionID sn, int pages, int offset, int bodyLen) {
        super(data);
        this.type = type;
        this.sn = sn;
        this.pages = pages;
        this.offset = offset;
        this.bodyLength = bodyLen;
    }

    public boolean isResponse() {
        return type.isResponse();
    }
    public boolean isFragment() {
        return type.isFragment();
    }
    public boolean isCommand() {
        return type.isCommand();
    }
    public boolean isCommandResponse() {
        return type.isCommandResponse();
    }
    public boolean isMessage() {
        return type.isMessage();
    }
    public boolean isMessageResponse() {
        return type.isMessageResponse();
    }
    public boolean isMessageFragment() {
        return type.isMessageFragment();
    }

    private static DataType getDataType(ByteArray data) {
        if (data.getSize() < 4) {
            // waiting for more data
            return null;
        }
        if (data.getByte(0) != MAGIC_CODE[0] ||
                data.getByte(1) != MAGIC_CODE[1] ||
                data.getByte(2) != MAGIC_CODE[2]) {
            //throw new IllegalArgumentException("not a DIM package: " + Arrays.toString(data));
            return null;
        }
        return DataType.from(data.slice(3, 4));
    }
    private static int getHeaderLength(ByteArray data) {
        // header length shared the byte with data type
        byte ch = data.getByte(3);
        int len = (ch & 0xF0) >> 4;
        if (len < 1 || len > 6) {
            return 0;
        } else {
            return len << 2;  // in bytes
        }
    }

    //
    //  Factories
    //

    public static Header parse(final ByteArray data) {
        // get data type
        DataType type = getDataType(data);
        if (type == null) {
            // not a DIM package?
            return null;
        }
        // get header length
        int headLen = getHeaderLength(data);
        if (data.getSize() < headLen) {
            // waiting for more data
            return null;
        }
        TransactionID sn;
        int pages = 1;
        int offset = 0;
        int bodyLen = -1;
        switch (headLen) {
            case 4: {
                /*  simple header (for UDP only)
                 *
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 */
                sn = TransactionID.ZERO;
                break;
            }
            case 8: {
                /*  simple header with body length
                 *
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |                 Body Length (32 bits) OPTIONAL                |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 */
                sn = TransactionID.ZERO;
                bodyLen = IntegerData.getInt32Value(data, 4);
                break;
            }
            case 12: {
                /*  command/message header without body length (for UDP only)
                 *
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |                    Transaction ID (64 bits)
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *                             Transaction ID (64 bits)                   |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 */
                sn = TransactionID.from(data.slice(4, 12));
                break;
            }
            case 16: {
                /*  command/message header with body length
                 *
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |      'D'      |      'I'      |      'M'      | H-Len |  Type |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |                    Transaction ID (64 bits)
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *                             Transaction ID (64 bits)                   |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 *        |                 Body Length (32 bits) OPTIONAL                |
                 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                 */
                sn = TransactionID.from(data.slice(4, 12));
                bodyLen = IntegerData.getInt32Value(data, 12);
                break;
            }
            case 20: {
                /*  fragment header without body length (for UDP only)
                 *
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
                 */
                sn = TransactionID.from(data.slice(4, 12));
                pages = IntegerData.getInt32Value(data, 12);
                offset = IntegerData.getInt32Value(data, 16);
                break;
            }
            case 24: {
                /*  fragment header with body length
                 *
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
                 */
                sn = TransactionID.from(data.slice(4, 12));
                pages = IntegerData.getInt32Value(data, 12);
                offset = IntegerData.getInt32Value(data, 16);
                bodyLen = IntegerData.getInt32Value(data, 20);
                break;
            }
            default: {
                //throw new NullPointerException("head length error: " + headLen);
                return null;
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
        return new Header(data.slice(0, headLen), type, sn, pages, offset, bodyLen);
    }

    //
    //  Factories
    //

    public static Header create(DataType type, TransactionID sn, int pages, int offset, int bodyLen) {
        assert type != null : "data type should not be null";
        assert sn != null : "transaction ID should not be null, use TransactionID.ZERO instead";
        assert 0 <= offset && offset < pages : "pages error: " + pages + ", " + offset;
        assert -1 <= bodyLen && bodyLen <= MAX_BODY_LENGTH : "body length error: " + bodyLen;
        int headLen = 4;  // in bytes
        if (TransactionID.ZERO.equals(sn)) {
            // simple header
            sn = null;
        } else {
            headLen += sn.getSize();  // 8 bytes
        }
        ByteArray options;
        if (type.isFragment()) {
            // message fragment (or its respond)
            assert pages > 1 : "fragment pages error: " + pages + ", " + offset;
            ByteArray d1 = IntegerData.getUInt32Data(pages);
            ByteArray d2 = IntegerData.getUInt32Data(offset);
            ByteArray d3 = bodyLen < 0 ? null : IntegerData.getUInt32Data(bodyLen);
            options = d1.concat(d2).concat(d3);
            headLen += options.getSize();  // 8 or 12 bytes
        } else if (bodyLen < 0) {
            // command/message (or its response, UDP only)
            options = null;
        } else {
            // command/message (or its respond)
            assert pages == 1 : "pages error: " + pages + ", " + offset;
            options = IntegerData.getUInt32Data(bodyLen);
            headLen += options.getSize();  // 4 bytes
        }
        // generate header data
        MutableData data = new MutableData(headLen);
        data.append(MAGIC_CODE);  // 'DIM'
        data.append((byte) ((headLen << 2) | (type.value & 0x0F)));
        if (sn != null) {
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
