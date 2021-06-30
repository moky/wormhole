/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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

import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 *  Package(s) to sent out (waiting response)
 */
public class Departure {

    /**
     *  Departure task will be expired after 2 minutes if no response received.
     */
    public static long EXPIRES = 120 * 1000; // milliseconds

    private final List<Package> packages;

    public final DataType type;
    public final TransactionID sn;

    public final SocketAddress remote;

    private int maxRetries = 3;  // totally 4 times to be sent at the most
    private long lastTime = 0;  // last send/receive timestamp (in milliseconds)

    public Departure(List<Package> fragments, SocketAddress target) {
        super();
        assert fragments.size() > 0 : "departure packages should not be empty";
        Package first = fragments.get(0);
        packages = fragments;
        type = first.head.type;
        sn = first.head.sn;
        remote = target;
    }
    public Departure(Package pack, SocketAddress target) {
        super();
        packages = new ArrayList<>();
        packages.add(pack);
        type = pack.head.type;
        sn = pack.head.sn;
        remote = target;
    }

    public boolean isExpired(long now) {
        return maxRetries >= 0 && (lastTime + EXPIRES) < now;
    }

    public synchronized List<Package> getFragments() {
        if (maxRetries < 0) {
            // retried too many times
            return null;
        } else if (packages.size() == 0) {
            // all fragments sent
            return null;
        } else {
            // update sending time
            lastTime = (new Date()).getTime();
            --maxRetries;
            // return the rest fragments
            return new ArrayList<>(packages);
        }
    }

    public synchronized boolean deleteFragment(int offset) {
        int index;
        int total = packages.size();
        for (index = 0; index < total; ++index) {
            if (packages.get(index).head.offset == offset) {
                // got it!
                packages.remove(index);
                break;
            }
        }
        if (packages.size() == 0) {
            // all fragments sent, remove this task
            return true;
        } else if (packages.size() < total) {
            // update receive time
            lastTime = (new Date()).getTime();
            return false;
        } else {
            // fragment not match
            return false;
        }
    }
}
