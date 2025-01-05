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

import java.util.Date;
import java.util.List;

import chat.dim.port.Arrival;
import chat.dim.startrek.ArrivalShip;
import chat.dim.type.ByteArray;

public class PackageArrival extends ArrivalShip {

    // head & body of the received package (or first fragment)
    private final Header head;
    private final ByteArray body;

    private final Packer packer;
    private Package completed;

    public PackageArrival(Package pack, Date now) {
        super(now);
        head = pack.head;
        body = pack.body;
        if (pack.isFragment()) {
            packer = new Packer(head.sn, head.pages);
            completed = packer.insert(pack);
        } else {
            packer = null;
            completed = pack;
        }
    }
    public PackageArrival(Package pack) {
        this(pack, new Date());
    }

    @Override
    public String toString() {
        String cname = getClass().getName();
        return "<" + cname + " size=" + completed.getSize() + " />";
    }

    public Package getPackage() {
        return completed;
    }

    @Override
    public TransactionID getSN() {
        return head.sn;
    }

    @Override
    public boolean equals(Object other) {
        if (super.equals(other)) {
            return true;
        } else if (other instanceof PackageArrival) {
            PackageArrival ship = (PackageArrival) other;
            return head.equals(ship.head) && body.equals(ship.body);
        } else {
            return false;
        }
    }

    @Override
    public int hashCode() {
        return head.hashCode() * 13 + body.hashCode();
    }

    @Override
    public Arrival assemble(Arrival income) {
        if (completed == null && income != this) {
            assert income instanceof PackageArrival : "arrival ship error: " + income;
            List<Package> fragments = ((PackageArrival) income).getFragments();
            assert fragments != null && fragments.size() > 0 : "fragments error: " + income;
            for (Package item : fragments) {
                completed = packer.insert(item);
            }
        }
        if (completed == null) {
            // extend expired time, wait for more fragments
            return null;
        } else {
            // package completed
            return this;
        }
    }

    List<Package> getFragments() {
        return packer == null ? null : packer.getFragments();
    }
}
