/* license: https://mit-license.org
 *
 *  Star Gate: Interfaces for network connection
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
package chat.dim.stargate;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 *  Star Dock
 *  ~~~~~~~~~
 *
 *  Parking Star Ships
 */
public class Dock {

    // tasks for sending out
    private final List<Integer> priorities = new ArrayList<>();
    private final Map<Integer, List<StarShip>> fleets = new HashMap<>();

    /**
     *  Park this ship in the Dock for departure
     *
     * @param task - outgo ship
     * @return false on duplicated
     */
    public boolean put(StarShip task) {
        // 1. choose an array with priority
        int prior = task.priority;
        List<StarShip> array = fleets.get(prior);
        if (array == null) {
            // 1.1. create new array for this priority
            array = new ArrayList<>();
            fleets.put(prior, array);
            // 1.2. insert the priority in a sorted list
            int index = 0;
            for (; index < priorities.size(); ++index) {
                if (prior < priorities.get(index)) {
                    // insert priority before the bigger one
                    break;
                }
            }
            priorities.add(index, prior);
        }
        // 2. check duplicated task
        for (StarShip item : array) {
            if (item == task) {
                return false;
            }
        }
        // 3. append to the tail
        array.add(task);
        return true;
    }

    /**
     *  Get next new ship, remove it from the park
     *
     * @return outgo ship
     */
    public StarShip pop() {
        List<StarShip> array;
        for (int prior : priorities) {
            array = fleets.get(prior);
            if (array == null) {
                continue;
            }
            for (StarShip ship : array) {
                if (ship.getTimestamp() == 0) {
                    // update time and try
                    ship.update();
                    array.remove(ship);
                    return ship;
                }
            }
        }
        return null;
    }

    /**
     *  Get ship with ID, remove it from the park
     *
     * @param sn - ship ID
     * @return outgo ship
     */
    public StarShip pop(byte[] sn) {
        List<StarShip> array;
        for (int prior : priorities) {
            array = fleets.get(prior);
            if (array == null) {
                continue;
            }
            for (StarShip ship : array) {
                if (Arrays.equals(ship.getSN(), sn)) {
                    // just remove it
                    array.remove(ship);
                    return ship;
                }
            }
        }
        return null;
    }

    /**
     *  Get any ship timeout/expired
     *    1. if expired, remove it from the park;
     *    2. else, update time and retry (keep it in the park)
     *
     * @return outgo ship
     */
    public StarShip any() {
        long expired = (new Date()).getTime() - StarShip.EXPIRES;
        List<StarShip> array;
        for (int prior : priorities) {
            array = fleets.get(prior);
            if (array == null) {
                continue;
            }
            for (StarShip ship : array) {
                if (ship.getTimestamp() > expired) {
                    // not expired yet
                    continue;
                }
                if (ship.getRetries() <= StarShip.RETRIES) {
                    // update time and retry
                    ship.update();
                    return ship;
                }
                // retried too may times
                if (ship.isExpired()) {
                    // task expired, remove it and don't retry
                    array.remove(ship);
                    return ship;
                }
            }
        }
        return null;
    }
}
