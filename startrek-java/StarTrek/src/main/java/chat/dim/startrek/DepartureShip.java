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

import chat.dim.port.Arrival;
import chat.dim.port.Departure;

public abstract class DepartureShip<A extends Arrival<A, I>, I> implements Departure<A, I> {

    /**
     *  Departure task will be expired after 2 minutes if no response received.
     */
    public static long EXPIRES = 120 * 1000; // milliseconds

    /**
     *  Departure task will be retried 2 times if timeout
     */
    public static int MAX_RETRIES = 2;

    private long lastTime;
    private int retries;

    private final int priority;

    protected DepartureShip(final int prior) {
        super();
        lastTime = 0;  // last tried time (timestamp in milliseconds)
        retries = -1;  // totally 3 times to be sent at the most
        priority = prior;
    }

    @Override
    public int getPriority() {
        return priority;
    }

    @Override
    public int getRetries() {
        return retries;
    }

    @Override
    public boolean isTimeout(final long now) {
        return retries < MAX_RETRIES && now > lastTime + EXPIRES;
    }

    @Override
    public boolean isFailed(final long now) {
        return now > lastTime + EXPIRES * (MAX_RETRIES - retries + 2);
    }

    @Override
    public boolean update(final long now) {
        if (retries >= MAX_RETRIES) {
            // retried too many times
            return false;
        }
        // update retried time
        lastTime = now;
        // decrease counter
        ++retries;
        return true;
    }
}
