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

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

import chat.dim.port.Arrival;
import chat.dim.port.Departure;

/**
 *  Memory cache for Departures
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public class DepartureHall {

    // tasks for sending out
    private final List<Integer> priorities = new ArrayList<>();
    private final Map<Integer, List<Departure>> departureFleets = new HashMap<>();

    private final Map<Object, Departure> departureMap = new WeakHashMap<>();
    private final Map<Object, Long> departureFinished = new HashMap<>();  // ID -> timestamp

    /**
     *  Append outgoing ship to a fleet with priority
     *
     * @param ship - departure task
     * @return false on duplicated
     */
    public boolean appendDeparture(final Departure ship) {
        final int priority = ship.getPriority();
        // 1. choose an array with priority
        List<Departure> fleet = departureFleets.get(priority);
        if (fleet == null) {
            // 1.1. create new array for this priority
            fleet = new ArrayList<>();
            departureFleets.put(priority, fleet);
            // 1.2. insert the priority in a sorted list
            insertPriority(priority);
        } else {
            // 1.3. check duplicated task
            if (fleet.contains(ship)) {
                return false;
            }
        }
        // 2. append to the tail
        fleet.add(ship);
        // 3. build mapping if SN exists
        final Object sn = ship.getSN();
        if (sn != null) {
            departureMap.put(sn, ship);
        }
        return true;
    }
    private void insertPriority(final int priority) {
        int total = priorities.size();
        int index = 0, value;
        // seeking position for new priority
        for (; index < total; ++index) {
            value = priorities.get(index);
            if (value == priority) {
                // duplicated
                return;
            } else if (value > priority) {
                // got it
                break;
            }
            // current value is smaller than the new value,
            // keep going
        }
        // insert new value before the bigger one
        priorities.add(index, priority);
    }

    /**
     *  Check response from incoming ship
     *
     * @param response - incoming ship with SN
     * @return finished task
     */
    public Departure checkResponse(final Arrival response) {
        Departure finished = null;
        final Object sn = response.getSN();
        assert sn != null : "SN not found: " + response;
        // check whether this task has already finished
        final Long time = departureFinished.get(sn);
        if (time == null || time == 0) {
            // check departure
            final Departure ship = departureMap.get(sn);
            if (ship != null && ship.checkResponse(response)) {
                // all fragments sent, departure task finished
                finished = ship;
                // remove it and clear mapping when SN exists
                remove(ship, sn);
                // mark finished time
                departureFinished.put(sn, (new Date()).getTime());
            }
        }
        return finished;
    }
    private void remove(final Departure ship, final Object sn) {
        final int priority = ship.getPriority();
        final List<Departure> fleet = departureFleets.get(priority);
        if (fleet != null) {
            fleet.remove(ship);
            // remove array when empty
            if (fleet.size() == 0) {
                departureFleets.remove(priority);
            }
        }
        // remove mapping by SN
        departureMap.remove(sn);
    }

    /**
     *  Get next new/timeout task
     *
     * @param now - current time
     * @return departure task
     */
    public Departure getNextDeparture(final long now) {
        // task.retries == 0
        Departure next = getNextNewDeparture(now);
        if (next == null) {
            // task.retries <= MAX_RETRIES and timeout
            next = getNextTimeoutDeparture(now);
        }
        return next;
    }
    private Departure getNextNewDeparture(final long now) {
        List<Departure> fleet;
        Iterator<Departure> iterator;
        Departure ship;
        Object sn;
        for (int priority : priorities) {
            // 1. get tasks with priority
            fleet = departureFleets.get(priority);
            if (fleet == null) {
                continue;
            }
            // 2. seeking new task in this priority
            iterator = fleet.iterator();
            while (iterator.hasNext()) {
                ship = iterator.next();
                if (ship.getRetries() == -1 && ship.update(now)) {
                    // first time to try, update and remove from the queue
                    iterator.remove();
                    sn = ship.getSN();
                    if (sn != null) {
                        departureMap.remove(sn);
                    }
                    return ship;
                }
            }
        }
        return null;
    }
    private Departure getNextTimeoutDeparture(final long now) {
        List<Departure> fleet;
        Iterator<Departure> iterator;
        Departure ship;
        Object sn;
        for (int priority : priorities) {
            // 1. get tasks with priority
            fleet = departureFleets.get(priority);
            if (fleet == null) {
                continue;
            }
            // 2. seeking timeout task in this priority
            iterator = fleet.iterator();
            while (iterator.hasNext()) {
                ship = iterator.next();
                if (ship.isTimeout(now) && ship.update(now)) {
                    // respond time out, update and remove from the queue
                    iterator.remove();
                    sn = ship.getSN();
                    if (sn != null) {
                        departureMap.remove(sn);
                    }
                    return ship;
                } else if (ship.isFailed(now)) {
                    // task expired, remove this ship
                    iterator.remove();
                    sn = ship.getSN();
                    if (sn != null) {
                        departureMap.remove(sn);
                    }
                }
            }
        }
        return null;
    }

    /**
     *  Clear all expired tasks
     */
    public void purge() {
        final Set<Departure> failedTasks = new HashSet<>();
        final long now = (new Date()).getTime();
        List<Departure> fleet;
        for (int priority : priorities) {
            // 0. get tasks with priority
            fleet = departureFleets.get(priority);
            if (fleet == null) {
                continue;
            }
            failedTasks.clear();
            // 1. seeking expired tasks in this priority
            for (Departure ship : fleet) {
                if (ship.isFailed(now)) {
                    // task expired
                    failedTasks.add(ship);
                }
            }
            // 2. clear expired tasks
            if (failedTasks.size() > 0) {
                clear(fleet, failedTasks, priority);
            }
        }
    }
    private void clear(List<Departure> fleet, final Set<Departure> failedTasks, final int priority) {
        Object sn;
        // remove expired tasks
        for (Departure ship : failedTasks) {
            fleet.remove(ship);
            // remove mapping when SN exists
            sn = ship.getSN();
            if (sn != null) {
                departureMap.remove(sn);
            }
            // TODO: callback?
        }
        // remove array when empty
        if (fleet.size() == 0) {
            departureFleets.remove(priority);
        }
    }
}
