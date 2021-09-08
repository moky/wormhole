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
import java.util.Iterator;
import java.util.List;

import chat.dim.port.Arrival;
import chat.dim.startrek.DepartureShip;

public class PackageDeparture extends DepartureShip {

    private final Package completed;

    private final List<Package> packages;
    private final List<byte[]> fragments;

    public PackageDeparture(int prior, Package pack) {
        super(prior);
        completed = pack;
        if (pack.isMessage()) {
            packages = Packer.split(pack);
        } else {
            packages = new ArrayList<>();
            packages.add(pack);
        }
        fragments = new ArrayList<>();
    }

    public Package getPackage() {
        return completed;
    }

    @Override
    public TransactionID getSN() {
        return completed.head.sn;
    }

    @Override
    public List<byte[]> getFragments() {
        if (fragments.size() == 0 && packages.size() > 0) {
            for (Package pack : packages) {
                fragments.add(pack.getBytes());
            }
        }
        return fragments;
    }

    @Override
    public boolean checkResponse(Arrival response) {
        int count = 0;
        assert response instanceof PackageArrival : "arrival ship error: " + response;
        PackageArrival ship = (PackageArrival) response;
        List<Package> array = ship.getFragments();
        if (array == null) {
            // it's a completed data package
            Package pack = ship.getPackage();
            if (removePage(pack.head.index)) {
                ++count;
            }
        } else {
            for (Package pack : array) {
                if (removePage(pack.head.index)) {
                    ++count;
                }
            }
        }
        if (count == 0) {
            return false;
        }
        fragments.clear();
        return true;
    }
    private boolean removePage(int index) {
        Iterator<Package> iterator = packages.iterator();
        while (iterator.hasNext()) {
            if (iterator.next().head.index == index) {
                // got it
                iterator.remove();
                return true;
            }
        }
        return false;
    }
}
