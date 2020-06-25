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
import chat.dim.tlv.IntData;

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
 *            If data type is a fragment message (or respond), there is a field
 *            'count' following the transaction ID, which indicates the message
 *            was split to how many fragments; and there is another field 'offset'
 *            following the 'count'; after them is the message fragment.
 */
public class Header extends Data {

    public final int headLength;
    public final DataType type;
    public final TransactionID sn;
    public final int pages;
    public final int offset;

    /**
     *  Create package header
     *
     * @param data    - header data as bytes
     * @param headLen - length of header (in bytes)
     * @param type    - package body data type
     * @param sn      - transaction ID
     * @param pages   - fragment count [OPTIONAL], default is 1
     * @param offset  - fragment index [OPTIONAL], default is 0
     */
    public Header(byte[] data, int headLen, DataType type, TransactionID sn, int pages, int offset) {
        super(data);
        this.headLength = headLen;
        this.type = type;
        this.sn = sn;
        this.pages = pages;
        this.offset = offset;
    }

    public Header(byte[] data, int headLen, DataType type, TransactionID sn) {
        this(data, headLen, type, sn, 1, 0);
    }

    public static Header parse(byte[] data) {
        int length = data.length;
        if (length < 12) {
            //throw new ArrayIndexOutOfBoundsException("package error: " + Arrays.toString(data));
            return null;
        }
        if (data[0] != 'D' || data[1] != 'I' || data[2] != 'M') {
            //throw new IllegalArgumentException("not a DIM package: " + Arrays.toString(data));
            return null;
        }
        // get header length & data type
        byte ch = data[3];
        int headLen = (ch & 0xF0) >> 2; // in bytes
        DataType type = DataType.getInstance(ch & 0x0F);
        int pos = 4;
        // get transaction ID
        TransactionID sn = TransactionID.parse(slice(data, pos));
        pos += sn.data.length;
        // get fragments count & offset
        int pages = 1;
        int offset = 0;
        if (type.equals(DataType.MessageFragment)) {
            pages = (int) IntData.bytesToInt(slice(data, pos, pos + 4));
            offset = (int) IntData.bytesToInt(slice(data, pos + 4, pos + 8));
            pos += 8;
        }
        return new Header(slice(data, 0, pos), headLen, type, sn, pages, offset);
    }

    //
    //  Factories
    //

    public static Header create(DataType type, TransactionID sn, int pages, int offset) {
        byte[] options;
        int headLen;
        if (type.equals(DataType.MessageFragment)) {
            byte[] a1 = IntData.intToBytes(pages, 4);
            byte[] a2 = IntData.intToBytes(offset, 4);
            options = concat(a1, a2);
            headLen = 20; // in bytes
        } else {
            options = new byte[0];
            headLen = 12; // in bytes
        }
        if (sn == null) {
            // generate transaction ID
            sn = TransactionID.create();
        }
        // generate header data
        byte hl_ty = (byte) (((headLen << 2) | (type.value & 0x0F)) & 0xFF);
        byte[] data = new byte[headLen];
        data[0] = 'D';
        data[1] = 'I';
        data[2] = 'M';
        data[3] = hl_ty;
        System.arraycopy(sn.data, 0, data, 4, sn.data.length);
        if (options.length > 0) {
            System.arraycopy(options, 0, data, 4 + sn.data.length, options.length);
        }
        return new Header(data, headLen, type, sn, pages, offset);
    }

    public static Header create(DataType type, int pages, int offset) {
        return create(type, null, pages, offset);
    }

    public static Header create(DataType type, TransactionID sn) {
        return create(type, sn, 1, 0);
    }

    public static Header create(DataType type) {
        return create(type, null, 1, 0);
    }
}
