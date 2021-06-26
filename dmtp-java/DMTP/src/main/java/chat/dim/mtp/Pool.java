/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
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
package chat.dim.mtp;

import java.net.SocketAddress;
import java.util.List;

import chat.dim.mtp.task.Arrival;
import chat.dim.mtp.task.Assemble;
import chat.dim.mtp.task.Departure;

/**
 *  Task Pool
 *  ~~~~~~~~~
 *
 *  Cache for departure, arrival tasks and message fragments
 */
public interface Pool {

    //
    //  Departures
    //

    /**
     *  Append a departure task into the pool after sent.
     *  This should be removed after its response received; if timeout, send it
     *  again and check it's retries counter, when it's still greater than 0,
     *  put it back to the pool for resending.
     *
     * @param task - depature task
     * @return false on failed
     */
    boolean appendDeparture(Departure task);

    /**
     *  Delete the departure task with 'trans_id' in the response.
     *  If it's a message fragment, check the page offset too.
     *
     * @param response    - respond package
     * @param destination - remote IP and port
     * @param source      - local IP and port
     * @return false on task not found/not finished yet
     */
    boolean deleteDeparture(Package response, SocketAddress destination, SocketAddress source);

    /**
     *  Gat one departure task from the pool for sending.
     *
     * @return any expiring departure task (removed from pool)
     */
    Departure shiftExpiredDeparture();

    //
    //  Arrivals
    //

    /**
     *  Append an arrival task into the pool after received something
     *
     * @param task - arrival task
     * @return false on failed
     */
    boolean appendArrival(Arrival task);

    /**
     *  Check how many arrivals waiting in the pool
     *
     * @return arrivals count
     */
    int numberOfArrivals();

    /**
     *  Get one arrival task from the pool for processing
     *
     * @return the first arrival task (removed from pool)
     */
    Arrival shiftFirstArrival();

    //
    //  Fragments Assembling
    //

    /**
     *  Add a fragment package into the pool for MessageFragment received.
     *  This will just wait until all fragments with the same 'trans_id' received.
     *  When all fragments received, they will be sorted and combined to the
     *  original message, and then return the message's data; if there are still
     *  some fragments missed, return None.
     *
     * @param fragment    - message fragment
     * @param source      - remote IP and port
     * @param destination - local IP and port
     * @return original message package when all fragments received
     */
    Package insertFragment(Package fragment, SocketAddress source, SocketAddress destination);

    /**
     *  Remove all expired fragments that belong to the incomplete messages,
     *  which had waited a long time but still some fragments missed.
     *
     * @return assembling tasks
     */
    List<Assemble> discardFragments();
}
