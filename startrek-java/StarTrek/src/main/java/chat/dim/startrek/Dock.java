/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.startrek;

import java.util.Date;

import chat.dim.port.Arrival;
import chat.dim.port.Departure;

/**
 *  Star Dock
 *  ~~~~~~~~~
 *
 *  Parking Star Ships
 */
public class Dock {

    // memory caches
    private final ArrivalHall arrivalHall;
    private final DepartureHall departureHall;

    public Dock() {
        super();
        arrivalHall = createArrivalHall();
        departureHall = createDepartureHall();
    }

    // override for user-customized hall
    protected ArrivalHall createArrivalHall() {
        return new ArrivalHall();
    }

    // override for user-customized hall
    protected DepartureHall createDepartureHall() {
        return new DepartureHall();
    }

    /**
     * Check received ship for completed package
     *
     * @param income - received ship carrying data package (fragment)
     * @return ship carrying completed data package
     */
    public Arrival assembleArrival(Arrival income) {
        // check fragment from income ship,
        // return a ship with completed package if all fragments received
        return arrivalHall.assembleArrival(income);
    }

    /**
     *  Add outgoing ship to the waiting queue
     *
     * @param outgo - departure task
     * @return false on duplicated
     */
    public boolean addDeparture(Departure outgo) {
        return departureHall.addDeparture(outgo);
    }

    /**
     *  Check response from incoming ship
     *
     * @param response - incoming ship with SN
     * @return finished task
     */
    public Departure checkResponse(Arrival response) {
        // check departure tasks with SN
        // remove package/fragment if matched (check page index for fragments too)
        return departureHall.checkResponse(response);
    }

    /**
     *  Get next new/timeout task
     *
     * @param now - current time
     * @return departure task
     */
    public Departure getNextDeparture(Date now) {
        // this will be remove from the queue,
        // if needs retry, the caller should append it back
        return departureHall.getNextDeparture(now);
    }

    /**
     * Clear all expired tasks
     */
    public int purge(Date now) {
        int count = 0;
        count += arrivalHall.purge(now);
        count += departureHall.purge(now);
        return count;
    }
}
