/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.startrek;

import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import chat.dim.port.Arrival;
import chat.dim.port.Ship;
import chat.dim.type.WeakMap;

/**
 *  Memory cache for Arrivals
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public class ArrivalHall {

    private final Set<Arrival> arrivals = new HashSet<>();
    private final Map<Object, Arrival> arrivalMap = new WeakMap<>();    // SN => ship
    private final Map<Object, Date> arrivalFinished = new HashMap<>();  // SN => timestamp

    /**
     *  Check received ship for completed package
     *
     * @param income - received ship carrying data package (fragment)
     * @return ship carrying completed data package
     */
    public Arrival assembleArrival(Arrival income) {
        // 1. check ship ID (SN)
        Object sn = income.getSN();
        if (sn == null) {
            // separated package ship must have SN for assembling
            // we consider it to be a ship carrying a whole package here
            return income;
        }
        // 2. check cached ship
        Arrival completed;
        Arrival cached = arrivalMap.get(sn);
        if (cached == null) {
            // check whether the task has already finished
            Date time = arrivalFinished.get(sn);
            if (time != null) {
                // task already finished
                return null;
            }
            // 3. new arrival, try assembling to check whether a fragment
            completed = income.assemble(income);
            if (completed == null) {
                // it's a fragment, waiting for more fragments
                arrivals.add(income);
                arrivalMap.put(sn, income);
                //income.touch(new Date());
            }
            // else, it's a completed package
        } else {
            // 3. cached ship found, try assembling (insert as fragment)
            //    to check whether all fragments received
            completed = cached.assemble(income);
            if (completed == null) {
                // it's not completed yet, update expired time
                // and wait for more fragments.
                cached.touch(new Date());
            } else {
                // all fragments received, remove cached ship
                arrivals.remove(cached);
                arrivalMap.remove(sn);
                // mark finished time
                arrivalFinished.put(sn, new Date());
            }
        }
        return completed;
    }

    /**
     *  Clear all expired tasks
     */
    public void purge(Date now) {
        if (now == null) {
            now = new Date();
        }
        // 1. seeking expired tasks
        Iterator<Arrival> ait = arrivals.iterator();
        Arrival ship;
        Object sn;
        while (ait.hasNext()) {
            ship = ait.next();
            if (ship.getStatus(now).equals(Ship.Status.EXPIRED)) {
                // task expired
                ait.remove(); //arrivals.remove(ship);
                // remove mapping with SN
                sn = ship.getSN();
                if (sn != null) {
                    arrivalMap.remove(sn);
                    // TODO: callback?
                }
            }
        }
        // 2. seeking neglected finished times
        Iterator<Map.Entry<Object, Date>> mit = arrivalFinished.entrySet().iterator();
        long ago = now.getTime() - 3600 * 1000;
        Map.Entry<Object, Date> entry;
        Date when;
        while (mit.hasNext()) {
            entry = mit.next();
            when = entry.getValue();
            if (when == null || when.getTime() < ago) {
                // long time ago
                mit.remove();
            }
        }
    }

}
