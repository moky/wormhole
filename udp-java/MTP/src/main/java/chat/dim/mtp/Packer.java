/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
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

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import chat.dim.type.ByteArray;
import chat.dim.type.MutableData;

public class Packer {

    private final List<Package> assembling = new ArrayList<>();
    private final int pages;
    public final TransactionID sn;

    private Package complete = null;

    public Packer(TransactionID sn, int pages) {
        super();
        this.sn = sn;
        this.pages = pages;
        assert pages > 1 : "pages error: " + pages;
    }

    public boolean isCompleted() {
        return assembling.size() == pages;
    }

    public Package getPackage() {
        if (complete == null && isCompleted()) {
            complete = join(assembling);
        }
        return complete;
    }

    public List<Package> getFragments() {
        return assembling;
    }

    public Package insert(Package fragment) {
        if (complete != null) {
            // already completed
            return complete;
        }
        Header head = fragment.head;
        assert head.sn.equals(sn) : "SN not match: " + sn + ", " + head.sn;
        assert head.type.isFragment() : "Packer only for fragments: " + head.type;
        assert head.pages == pages : "pages error: " + pages + ", " + head.pages;
        assert head.index < pages : "index error: " + head.index + ", " + pages;
        int count = assembling.size();
        int index = count - 1;
        Package item;
        for (; index >= 0; --index) {
            item = assembling.get(index);
            if (item.head.index < head.index) {
                // got the position
                break;
            } else if (item.head.index == head.index) {
                //throw new IllegalArgumentException("duplicated: " + item.head);
                return null;
            }
        }
        // insert after the position
        assembling.add(index + 1, fragment);
        return getPackage();
    }

    /*    Optimal Length for UDP package body
     *    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     *    MTU      : 576 bytes
     *    IP Head  : 20 bytes
     *    UDP Head : 8 bytes
     *    Header   : 12 bytes (excludes 'pages', 'index' and 'bodyLen')
     *    Reserved : 24 bytes (includes 'pages', 'index' and 'bodyLen')
     */
    public static int OPTIMAL_BODY_LENGTH = 512;

    /**
     *  Join sorted packages' body data together
     *
     * @param packages - packages sorted by index
     * @return original message package
     */
    public static Package join(final List<Package> packages) {
        int count = packages.size();
        assert count > 1 : "packages count error: " + count;
        Package first = packages.get(0);
        TransactionID sn = first.head.sn;
        // get fragments count
        int pages = first.head.pages;
        assert pages == count : "pages error: " + pages + ", " + count;
        // add message fragments part by part
        List<ByteArray> fragments = new ArrayList<>();
        int length = 0;
        int index;
        Package item;
        for (index = 0; index < count; ++index) {
            item = packages.get(index);
            assert item.head.type.isFragment() : "data type should be fragment: " + item;
            assert sn.equals(item.head.sn) : "transaction ID not match: " + item;
            assert pages == item.head.pages : "pages error: " + item;
            assert index == item.head.index : "fragment missed: " + index;
            fragments.add(item.body);
            length += item.body.getSize();
        }
        assert index == pages : "fragment error: " + index + ", " + pages;
        // join fragments
        MutableData data = new MutableData(length);
        for (index = 0; index < count; ++index) {
            data.append(fragments.get(index));
        }
        if (first.head.bodyLength < 0) {
            // UDP (unlimited)
            assert first.head.bodyLength == -1 : "body length error: " + first.head.bodyLength;
            return Package.create(DataType.MESSAGE, sn, 1, 0, -1, data);
        } else {
            // TCP (should not happen)
            return Package.create(DataType.MESSAGE, sn, 1, 0, data.getSize(), data);
        }
    }

    /**
     *  Split large message package
     *
     * @param pack - UDP package
     * @return message fragment packages
     */
    public static List<Package> split(final Package pack) {
        final Header head = pack.head;
        final ByteArray body = pack.body;
        assert head.type.isMessage() : "cannot split this type: " + head.type;
        // split body
        List<ByteArray> fragments = new ArrayList<>();
        int pages = 1;
        int start = 0, end = OPTIMAL_BODY_LENGTH;
        int bodySize = body.getSize();
        for (; end < bodySize; start = end, end += OPTIMAL_BODY_LENGTH) {
            fragments.add(body.slice(start, end));
            pages += 1;
        }
        if (start > 0) {
            fragments.add(body.slice(start)); // the tail
        } else {
            fragments.add(body);  // the whole body (too small)
        }
        // create packages with fragments
        List<Package> packages = new ArrayList<>();
        ByteArray data;
        if (pages == 1) {
            // package too small, no need to split
            assert fragments.size() == 1 : "fragments error: " + fragments.size() + ", " + pages;
            packages.add(pack);
        } else if (head.bodyLength < 0) {
            // UDP (unlimited)
            assert head.bodyLength == -1 : "body length error: " + head.bodyLength;
            for (int index = 0; index < pages; ++index) {
                data = fragments.get(index);
                packages.add(Package.create(DataType.MESSAGE_FRAGMENT, head.sn, pages, index, -1, data));
            }
        } else {
            // TCP (should not happen)
            for (int index = 0; index < pages; ++index) {
                data = fragments.get(index);
                packages.add(Package.create(DataType.MESSAGE_FRAGMENT, head.sn, pages, index, data.getSize(), data));
            }
        }
        return packages;
    }

    /**
     *  Sort the fragments with head.index
     *
     * @param packages - fragments
     * @return sorted fragments
     */
    public static List<Package> sort(List<Package> packages) {
        packages.sort(Comparator.comparingInt(Package::getFragmentIndex));
        return packages;
    }
}
