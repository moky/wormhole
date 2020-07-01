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
package chat.dim.mtp.task;

import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.mtp.protocol.DataType;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;

/**
 *  Message fragments received (waiting assemble)
 */
public class Assemble {

    public final List<Package> fragments = new ArrayList<>();

    public final SocketAddress source;
    public final SocketAddress destination;

    public final TransactionID sn;
    public final int pages;

    private float lastTime;  // last receive timestamp (in seconds)

    public Assemble(Package fragment, SocketAddress source, SocketAddress destination) {
        super();

        this.fragments.add(fragment);

        this.source = source;
        this.destination = destination;

        this.sn = fragment.head.sn;
        this.pages = fragment.head.pages;

        updateLastTime();
    }

    public boolean isCompleted() {
        return fragments.size() == pages;
    }

    public float getLastTime() {
        return lastTime;
    }
    public void updateLastTime() {
        lastTime = (new Date()).getTime() / 1000.0f;
    }

    public boolean insert(Package fragment, SocketAddress source, SocketAddress destination) {
        assert this.source.equals(source) : "source error: " + source + ", " + this.source;
        assert this.destination.equals(destination) : "destination error: " + destination + ", " + this.destination;
        int count = fragments.size();
        assert count > 0 : "fragments error";
        int offset = fragment.head.offset;
        assert DataType.MessageFragment.equals(fragment.head.type) : "data type error: " + fragment.head.type;
        assert sn.equals(fragment.head.sn) : "transaction ID not match:" + fragment.head.sn;
        assert pages == fragment.head.pages : "pages error: " + fragment.head.pages;
        assert offset < pages : "offset error: " + offset;
        Package item;
        int index = count - 1;
        for (; index >= 0; --index) {
            item = fragments.get(index);
            if (offset < item.head.offset) {
                continue;
            } else if (offset == item.head.offset) {
                //throw new IllegalArgumentException("duplicated: " + item.head);
                return false;
            }
            // got the position
            break;
        }
        // insert after it
        fragments.add(index + 1, fragment);
        updateLastTime();
        return true;
    }
}
