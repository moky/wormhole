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
import java.util.Date;
import java.util.List;

import chat.dim.mtp.Package;
import chat.dim.mtp.Packer;

/**
 *  Message fragments received (waiting assemble)
 */
public class Assemble {

    public final Packer packer;

    public final SocketAddress source;
    public final SocketAddress destination;

    private long lastTime;  // last receive timestamp (in milliseconds)

    public Assemble(Package fragment, SocketAddress from, SocketAddress to) {
        super();

        packer = new Packer(fragment.head.sn, fragment.head.pages);
        packer.insert(fragment);

        source = from;
        destination = to;

        updateLastTime();
    }

    public boolean isCompleted() {
        return packer.isCompleted();
    }

    public List<Package> getFragments() {
        return packer.getFragments();
    }

    public long getLastTime() {
        return lastTime;
    }
    public void updateLastTime() {
        lastTime = (new Date()).getTime();
    }

    public Package insert(Package fragment, SocketAddress source, SocketAddress destination) {
        assert this.source.equals(source) : "source error: " + source + ", " + this.source;
        assert this.destination.equals(destination) : "destination error: " + destination + ", " + this.destination;
        return packer.insert(fragment);
    }
}
