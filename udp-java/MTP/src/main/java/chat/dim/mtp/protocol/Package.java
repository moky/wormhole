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

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import chat.dim.tlv.Data;
import chat.dim.tlv.MutableData;

public class Package extends Data {

    /*    Optimal Length for UDP package body
     *    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     *    MTU      : 576 bytes
     *    IP Head  : 20 bytes
     *    UDP Head : 8 bytes
     *    Header   : 12 bytes (excludes 'pages', 'offset' and 'bodyLen')
     *    Reserved : 24 bytes (includes 'pages', 'offset' and 'bodyLen')
     */
    public static int OPTIMAL_BODY_LENGTH = 512;

    public final Header head;
    public final Data body;

    public Package(Data data, Header head, Data body) {
        super(data);
        this.head = head;
        this.body = body;
    }

    private int getFragmentOffset() {
        return head.offset;
    }

    /**
     *  Split large message package
     *
     * @return message fragment packages
     */
    public List<Package> split() {
        assert head.type.equals(DataType.Message) : "cannot split this type: " + head.type;
        // split body
        List<Data> fragments = new ArrayList<>();
        int count = 1;
        int start = 0, end = OPTIMAL_BODY_LENGTH;
        int length = body.getLength();
        for (; end < length; start = end, end += OPTIMAL_BODY_LENGTH) {
            fragments.add(body.slice(start, end));
            count += 1;
        }
        if (start > 0) {
            fragments.add(body.slice(start)); // the tail
        } else {
            fragments.add(body);
        }
        // create packages with fragments
        List<Package> packages = new ArrayList<>();
        DataType type = DataType.MessageFragment;
        TransactionID sn = head.sn;
        Data data;
        if (head.bodyLength < 0) {
            // UDP (unlimited)
            for (int index = 0; index < count; ++index) {
                data = fragments.get(index);
                packages.add(create(type, sn, count, index, -1, data));
            }
        } else {
            // TCP (should not happen)
            for (int index = 0; index < count; ++index) {
                data = fragments.get(index);
                packages.add(create(type, sn, count, index, data.getLength(), data));
            }
        }
        return packages;
    }

    /**
     *  Join sorted packages' body data together
     *
     * @param packages - packages sorted by offset
     * @return original message package
     */
    public static Package join(List<Package> packages) {
        int count = packages.size();
        assert count > 1 : "packages count error: " + count;
        Package first = packages.get(0);
        DataType type = DataType.MessageFragment;
        TransactionID sn = first.head.sn;
        // get fragments count
        int pages = first.head.pages;
        assert pages == count : "pages error: " + pages + ", " + count;
        // add message fragments part by part
        List<Data> fragments = new ArrayList<>();
        int length = 0;
        int index;
        Package item;
        for (index = 0; index < count; ++index) {
            item = packages.get(index);
            assert type.equals(item.head.type) : "data type should be fragment: " + item;
            assert sn.equals(item.head.sn) : "transaction ID not match: " + item;
            assert pages == item.head.pages : "pages error: " + item;
            assert index == item.head.offset : "fragment missed: " + index;
            fragments.add(item.body);
            length += item.body.getLength();
        }
        assert index == pages : "fragment error: " + index + ", " + pages;
        // join fragments
        MutableData data = new MutableData(length);
        Data fra;
        int pos;
        for (index = 0, pos = 0; index < count; ++index) {
            fra = fragments.get(index);
            data.copy(fra, 0, pos, fra.getLength());
            pos += fra.getLength();
        }
        type = DataType.Message;
        if (first.head.bodyLength < 0) {
            // UDP (unlimited)
            return create(type, sn, 1, 0, -1, data);
        } else {
            // TCP (should not happen)
            return create(type, sn, 1, 0, data.getLength(), data);
        }
    }

    public static List<Package> sort(List<Package> packages) {
        packages.sort(Comparator.comparingInt(Package::getFragmentOffset));
        return packages;
    }

    public static Package parse(Data data) {
        // get package head
        Header head = Header.parse(data);
        if (head == null) {
            //throw new NullPointerException("package head error: " + Arrays.toString(data));
            return null;
        }
        // check lengths
        int dataLen = data.getLength();
        int headLen = head.getLength();
        int bodyLen = head.bodyLength;
        if (bodyLen < 0) {
            // unlimited
            bodyLen = dataLen - headLen;
        }
        int packLen = headLen + bodyLen;
        if (dataLen < packLen) {
            //throw new ArrayIndexOutOfBoundsException("package length error: " + Arrays.toString(data));
            return null;
        } else if (dataLen > packLen) {
            data = data.slice(0, packLen);
        }
        // get body
        Data body;
        if (bodyLen == 0) {
            body = Data.ZERO;
        } else {
            body = data.slice(headLen);
        }
        return new Package(data, head, body);
    }

    //
    //  Factories
    //

    public static Package create(DataType type, TransactionID sn, int pages, int offset, int bodyLen, Data body) {
        assert body != null : "package body should not be null";
        // create package with header
        Header head = Header.create(type, sn, pages, offset, bodyLen);
        Data data;
        if (body.getLength() > 0) {
            data = head.concat(body);
        } else {
            data = head;
        }
        return new Package(data, head, body);
    }

    //
    //  UDP
    //

    public static Package create(DataType type, TransactionID sn, int pages, int offset, Data body) {
        return create(type, sn, pages, offset, -1, body);
    }

    public static Package create(DataType type, int pages, int offset, Data body) {
        return create(type, TransactionID.create(), pages, offset, -1, body);
    }

    public static Package create(DataType type, TransactionID sn, Data body) {
        return create(type, sn, 1, 0, -1, body);
    }

    public static Package create(DataType type, Data body) {
        return create(type, TransactionID.create(), 1, 0, -1, body);
    }

    //
    //  TCP
    //

    public static Package create(DataType type, TransactionID sn, int bodyLen , Data body) {
        assert bodyLen == body.getLength() : "body length error: " + bodyLen + ", " + body.getLength();
        return create(type, sn, 1, 0, bodyLen, body);
    }

    public static Package create(DataType type, int bodyLen, Data body) {
        assert bodyLen == body.getLength() : "body length error: " + bodyLen + ", " + body.getLength();
        return create(type, TransactionID.create(), 1, 0, bodyLen, body);
    }
}
