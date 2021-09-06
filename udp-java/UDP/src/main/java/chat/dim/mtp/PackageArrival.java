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

import chat.dim.port.Arrival;
import chat.dim.startrek.ArrivalShip;

import java.util.List;

public class PackageArrival extends ArrivalShip {

    private final TransactionID sn;

    private final Packer packer;
    private Package completed;

    public PackageArrival(Package pack) {
        super();
        sn = pack.head.sn;
        if (pack.isFragment()) {
            packer = new Packer(pack.head.sn, pack.head.pages);
            completed = packer.insert(pack);
        } else {
            packer = null;
            completed = pack;
        }
    }

    public Package getPackage() {
        return completed;
    }

    @Override
    public Object getSN() {
        return sn;
    }

    @Override
    public Arrival assemble(Arrival arrival) {
        if (completed == null) {
            assert arrival instanceof PackageArrival : "arrival ship error: " + arrival;
            List<Package> fragments = ((PackageArrival) arrival).getFragments();
            assert fragments != null && fragments.size() > 0 : "fragments error: " + arrival;
            for (Package item : fragments) {
                completed = packer.insert(item);
            }
        }
        return completed == null ? null : new PackageArrival(completed);
    }

    List<Package> getFragments() {
        return packer == null ? null : packer.getFragments();
    }
}
