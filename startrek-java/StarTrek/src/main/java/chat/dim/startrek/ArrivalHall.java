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
import java.util.WeakHashMap;

import chat.dim.port.Arrival;

/**
 *  Memory cache for Arrivals
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public class ArrivalHall {

    private final Set<Arrival> arrivals = new HashSet<>();
    private final Map<Object, Arrival> arrivalMap = new WeakHashMap<>();

    private final Map<Object, Long> arrivalFinished = new HashMap<>();  // ID -> timestamp

    /**
     *  Check received ship for completed package
     *
     * @param income - received ship carrying data package (fragment)
     * @return ship carrying completed data package
     */
    public Arrival assembleArrival(final Arrival income) {
        // check ship ID (SN)
        final Object sn = income.getSN();
        if (sn == null) {
            // separated package ship must have SN for assembling
            // we consider it to be a ship carrying a whole package here
            return income;
        }
        // check whether the task has already finished
        final Long time = arrivalFinished.get(sn);
        if (time != null && time > 0) {
            // task already finished
            return null;
        }
        Arrival task = arrivalMap.get(sn);
        if (task == null) {
            // new arrival, try assembling to check whether a fragment
            task = income.assemble(income);
            if (task == null) {
                // it's a fragment, waiting for more fragments
                arrivals.add(income);
                arrivalMap.put(sn, income);
                return null;
            } else {
                // it's a completed package
                return task;
            }
        }
        // insert as fragment
        final Arrival completed = task.assemble(income);
        if (completed == null) {
            // not completed yet, waiting for more fragments
            return null;
        }
        // all fragments received, remove this task
        arrivals.remove(task);
        arrivalMap.remove(sn);
        // mark finished time
        arrivalFinished.put(sn, (new Date()).getTime());
        return completed;
    }

    /**
     *  Clear all expired tasks
     */
    public void purge() {
        final Set<Arrival> failedTasks = new HashSet<>();
        final long now = (new Date()).getTime();
        // 1. seeking expired tasks
        for (Arrival ship : arrivals) {
            if (ship.isFailed(now)) {
                // task expired
                failedTasks.add(ship);
            }
        }
        // 2. clear expired tasks
        if (failedTasks.size() > 0) {
            Object sn;
            // remove expired tasks
            for (Arrival ship : failedTasks) {
                arrivals.remove(ship);
                // remove mapping with SN
                sn = ship.getSN();
                assert sn != null : "SN empty: " + ship;
                arrivalMap.remove(sn);
                // TODO: callback?
            }
        }
        // 3. seeking neglected finished times
        Iterator<Map.Entry<Object, Long>> it;
        it = arrivalFinished.entrySet().iterator();
        long ago = (new Date()).getTime() - 3600;
        Long when;
        while (it.hasNext()) {
            when = it.next().getValue();
            if (when == null || when < ago) {
                // long time ago
                it.remove();
            }
        }
    }
}
