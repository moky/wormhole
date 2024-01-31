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
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Ship;
import chat.dim.type.WeakMap;
import chat.dim.type.WeakSet;

/**
 *  Memory cache for Departures
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public class DepartureHall {

    // all departure ships
    private final Set<Departure> allDepartures = new WeakSet<>();

    // new ships waiting to send out
    private final List<Departure> newDepartures = new ArrayList<>();

    // ships waiting for responses
    private final Map<Integer, List<Departure>> departureFleets = new HashMap<>();  // priority => List[Departure]
    private final List<Integer> priorities = new ArrayList<>();

    // index
    private final Map<Object, Departure> departureMap = new WeakMap<>();      // SN => ship
    private final Map<Object, Long> departureFinished = new HashMap<>();      // SN => timestamp
    private final Map<Object, Integer> departureLevel = new WeakHashMap<>();  // SN => priority

    /**
     *  Add outgoing ship to the waiting queue
     *
     * @param outgo - departure task
     * @return false on duplicated
     */
    public boolean addDeparture(Departure outgo) {
        // 1. check duplicated
        if (allDepartures.contains(outgo)) {
            return false;
        } else {
            allDepartures.add(outgo);
        }
        // 2. insert to the sorted queue
        int priority = outgo.getPriority();
        int index;
        for (index = 0; index < newDepartures.size(); ++index) {
            if (newDepartures.get(index).getPriority() > priority) {
                // take the place before first ship
                // which priority is greater then this one.
                break;
            }
        }
        newDepartures.add(index, outgo);
        return true;
    }

    /**
     *  Check response from incoming ship
     *
     * @param response - incoming ship with SN
     * @return finished task
     */
    public Departure checkResponse(Arrival response) {
        Object sn = response.getSN();
        assert sn != null : "Ship SN not found: " + response;
        // check whether this task has already finished
        Long time = departureFinished.get(sn);
        if (time != null && time > 0) {
            return null;
        }
        // check departure
        Departure ship = departureMap.get(sn);
        if (ship != null && ship.checkResponse(response)) {
            // all fragments sent, departure task finished
            // remove it and clear mapping when SN exists
            removeShip(ship, sn);
            // mark finished time
            departureFinished.put(sn, System.currentTimeMillis());
            return ship;
        }
        return null;
    }
    private void removeShip(Departure ship, Object sn) {
        int priority = departureLevel.get(sn);
        List<Departure> fleet = departureFleets.get(priority);
        if (fleet != null) {
            fleet.remove(ship);
            // remove array when empty
            if (fleet.size() == 0) {
                departureFleets.remove(priority);
            }
        }
        // remove mapping by SN
        departureMap.remove(sn);
        departureLevel.remove(sn);
        allDepartures.remove(ship);
    }

    /**
     *  Get next new/timeout task
     *
     * @param now - current time
     * @return departure task
     */
    public Departure getNextDeparture(long now) {
        // task.expired == 0
        Departure next = getNextNewDeparture(now);
        if (next == null) {
            // task.expired < now
            next = getNextTimeoutDeparture(now);
        }
        return next;
    }
    private Departure getNextNewDeparture(long now) {
        if (newDepartures.size() == 0) {
            return null;
        }
        // get first ship
        Departure outgo = newDepartures.remove(0);
        Object sn = outgo.getSN();
        if (outgo.isImportant() && sn != null) {
            // this task needs response
            // choose an array with priority
            int priority = outgo.getPriority();
            insertShip(outgo, priority, sn);
            // build index for it
            departureMap.put(sn, outgo);
        } else {
            // disposable ship needs no response,
            // remove it immediately
            allDepartures.remove(outgo);
        }
        // update expired time
        outgo.touch(now);
        return outgo;
    }
    private void insertShip(Departure outgo, int priority, Object sn) {
        List<Departure> fleet = departureFleets.get(priority);
        if (fleet == null) {
            // create new array for this priority
            fleet = new ArrayList<>();
            departureFleets.put(priority, fleet);
            // insert the priority in a sorted list
            insertPriority(priority);
        }
        // append to the tail, and build index for it
        fleet.add(outgo);
        departureLevel.put(sn, priority);
    }
    private void insertPriority(int priority) {
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
    private Departure getNextTimeoutDeparture(long now) {
        List<Departure> fleet;
        Iterator<Departure> dit;
        Departure ship;
        Ship.Status status;
        Object sn;
        List<Integer> priorityList = new ArrayList<>(priorities);
        for (int priority : priorityList) {
            // 1. get tasks with priority
            fleet = departureFleets.get(priority);
            if (fleet == null) {
                continue;
            }
            // 2. seeking timeout task in this priority
            dit = fleet.iterator();
            while (dit.hasNext()) {
                ship = dit.next();
                sn = ship.getSN();
                assert sn != null : "Ship ID should not be empty here";
                status = ship.getStatus(now);
                if (status.equals(Ship.Status.TIMEOUT)) {
                    // response timeout, needs retry now.
                    // move to next priority
                    dit.remove();
                    insertShip(ship, priority + 1, sn);
                    // update expired time
                    ship.touch(now);
                    return ship;
                } else if (status.equals(Ship.Status.FAILED)) {
                    // try too many times and still missing response,
                    // task failed, remove this ship.
                    dit.remove();
                    // remove mapping by SN
                    departureMap.remove(sn);
                    departureLevel.remove(sn);
                    allDepartures.remove(ship);
                    return ship;
                }
            }
        }
        return null;
    }

    /**
     *  Clear all expired tasks
     */
    public void purge(long now) {
        // 1. seeking finished tasks
        Iterator<Integer> pit = priorities.iterator();
        int prior;
        List<Departure> fleet;
        Iterator<Departure> fit;
        Departure ship;
        Object sn;
        while (pit.hasNext()) {
            prior = pit.next();
            fleet = departureFleets.get(prior);
            if (fleet == null) {
                // this priority is empty
                pit.remove();
                continue;
            }
            fit = fleet.iterator();
            while (fit.hasNext()) {
                ship = fit.next();
                if (ship.getStatus(now).equals(Ship.Status.DONE)) {
                    // task done
                    fit.remove();
                    sn = ship.getSN();
                    assert sn != null : "Ship SN should not be empty here";
                    departureMap.remove(sn);
                    departureLevel.remove(sn);
                    // mark finished time
                    departureFinished.put(sn, now);
                }
            }
            // remove array when empty
            if (fleet.size() == 0) {
                departureFleets.remove(prior);
                pit.remove();
            }
        }
        // 2. seeking neglected finished times
        Iterator<Map.Entry<Object, Long>> mit = departureFinished.entrySet().iterator();
        long ago = now - 3600 * 1000;
        Map.Entry<Object, Long> entry;
        Long when;
        while (mit.hasNext()) {
            entry = mit.next();
            when = entry.getValue();
            if (when == null || when < ago) {
                // long time ago
                mit.remove();
            }
        }
    }
}
