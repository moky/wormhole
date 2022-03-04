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

import java.lang.ref.WeakReference;
import java.util.Date;

import chat.dim.port.Departure;

public abstract class DepartureShip implements Departure {

    /**
     *  Departure task will be expired after 2 minutes if no response received.
     */
    public static long EXPIRES = 120 * 1000; // milliseconds

    /**
     *  Departure task will be retried 2 times if timeout
     */
    public static int MAX_RETRIES = 2;

    private long expired;  // last tried time (timestamp in milliseconds)
    private int retries;   // totally 3 times to be sent at the most

    private final int priority;

    private final WeakReference<Delegate> delegateRef;

    protected DepartureShip(int prior, Delegate delegate, long now) {
        super();
        // ship priority
        priority = prior;

        // specific delegate for this ship
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }

        expired = now + EXPIRES;
        retries = -1;
    }
    protected DepartureShip(int prior, Delegate delegate) {
        this(prior, delegate, new Date().getTime());
    }

    public Delegate getDelegate() {
        return delegateRef == null ? null : delegateRef.get();
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
    public boolean isTimeout(long now) {
        return retries < MAX_RETRIES && expired < now;
    }

    @Override
    public boolean isFailed(long now) {
        long extra = EXPIRES * (MAX_RETRIES - retries);
        return expired + extra < now;
    }

    @Override
    public boolean update(long now) {
        if (retries >= MAX_RETRIES) {
            // retried too many times
            return false;
        }
        // update retried time
        expired = now + EXPIRES;
        // increase counter
        ++retries;
        return true;
    }
}
