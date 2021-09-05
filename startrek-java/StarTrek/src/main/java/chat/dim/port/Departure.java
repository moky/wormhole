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
package chat.dim.port;

import java.util.List;

/**
 *  Outgoing Ship
 *  ~~~~~~~~~~~~~
 */
public interface Departure extends Ship {

    enum Priority {
        URGENT (-1),
        NORMAL ( 0),
        SLOWER ( 1);

        public final int value;

        Priority(final int v) {
            value = v;
        }
    }

    int getPriority();

    /**
     *  Get retries
     *
     * @return tried times
     */
    int getRetries();

    /**
     *  Check whether task needs retry
     *
     * @param now - current time
     * @return true on retry
     */
    boolean isTimeout(final long now);

    /**
     *  Get fragments to sent
     *
     * @return remaining separated data packages
     */
    List<byte[]> getFragments();

    /**
     *  The received ship may carried a response for the departure
     *  if all fragments responded, means this task is finished.
     *
     * @param response - income ship carried with response
     * @return true on task finished
     */
    boolean checkResponse(final Arrival response);
}
