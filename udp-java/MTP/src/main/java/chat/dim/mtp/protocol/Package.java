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

public class Package extends Data {

    /*    Max Length for Package Body
     *    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
     *    MTU      : 576 bytes
     *    IP Head  : 20 bytes
     *    UDP Head : 8 bytes
     *    Header   : 12 bytes (excludes 'pages' and 'offset')
     *    Reserved : 24 bytes (includes 'pages' and 'offset')
     */
    public static int MAX_BODY_LEN = 512;

    public final Header head;
    public final byte[] body;

    public Package(byte[] data, Header head, byte[] body) {
        super(data);
        this.head = head;
        this.body = body;
    }

    private int getOffset() {
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
        List<byte[]> fragments = new ArrayList<>();
        int count = 1;
        int start = 0, end = MAX_BODY_LEN;
        int length = body.length;
        for (; end < length; start = end, end += MAX_BODY_LEN) {
            fragments.add(slice(body, start, end));
            count += 1;
        }
        if (start > 0) {
            fragments.add(slice(body, start)); // the tail
        } else {
            fragments.add(body);
        }
        // create packages with fragments
        List<Package> packages = new ArrayList<>();
        DataType type = DataType.MessageFragment;
        TransactionID sn = head.sn;
        for (int index = 0; index < count; ++index) {
            packages.add(create(type, sn, count, index, fragments.get(index)));
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
        List<byte[]> fragments = new ArrayList<>();
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
            length += item.body.length;
        }
        assert index == pages : "fragment error: " + index + ", " + pages;
        // join fragments
        byte[] buffer = new byte[length];
        byte[] fra;
        int pos;
        for (index = 0, pos = 0; index < count; ++index) {
            fra = fragments.get(index);
            System.arraycopy(fra, 0, buffer, pos, fra.length);
            pos += fra.length;
        }
        type = DataType.Message;
        return create(type, sn, buffer);
    }

    public static List<Package> sort(List<Package> packages) {
        packages.sort(Comparator.comparingInt(Package::getOffset));
        return packages;
    }

    public static Package parse(byte[] data) {
        // get package head
        Header head = Header.parse(data);
        if (head == null) {
            //throw new NullPointerException("package head error: " + Arrays.toString(data));
            return null;
        }
        // get package body
        byte[] body = slice(data, head.headLength);
        return new Package(data, head, body);
    }

    //
    //  Factories
    //

    public static Package create(DataType type, TransactionID sn, int pages, int offset, byte[] body) {
        if (body == null) {
            body = new byte[0];
        }
        // create package with header
        Header head = Header.create(type, sn, pages, offset);
        byte[] data = concat(head.data, body);
        return new Package(data, head, body);
    }

    public static Package create(DataType type, int pages, int offset, byte[] body) {
        return create(type, null, pages, offset, body);
    }

    public static Package create(DataType type, TransactionID sn, byte[] body) {
        return create(type, sn, 1, 0, body);
    }

    public static Package create(DataType type, byte[] body) {
        return create(type, null, 1, 0, body);
    }
}
