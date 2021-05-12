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

import java.lang.ref.WeakReference;
import java.util.Date;

public abstract class StarShip implements Ship {

    // retry
    public static int EXPIRES = 120 * 1000;  // 2 minutes
    public static int RETRIES = 2;

    // priorities
    public static final int URGENT = -1;
    public static final int NORMAL = 0;
    public static final int SLOWER = 1;

    public final int priority;

    // for retry
    private long timestamp = 0;  // last time
    private int retries = -1;

    private final WeakReference<Ship.Delegate> delegateRef;

    protected StarShip(int prior, Ship.Delegate delegate) {
        super();
        priority = prior;
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }

    /**
     *  Get handler for this Star Ship
     *
     * @return delegate
     */
    public Ship.Delegate getDelegate() {
        if (delegateRef == null) {
            return null;
        } else {
            return delegateRef.get();
        }
    }

    /**
     *  Get last time of trying
     *
     * @return timestamp
     */
    public long getTimestamp() {
        return timestamp;
    }

    /**
     *  Get count of retries
     *
     * @return count
     */
    public int getRetries() {
        return retries;
    }

    /**
     *  Check whether retry too many times and no response
     *
     * @return true on failure
     */
    public boolean isExpired() {
        long now = (new Date()).getTime();
        return now > timestamp + EXPIRES * (RETRIES + 2L);
    }

    /**
     *  Update retries count and time
     */
    public void update() {
        timestamp = (new Date()).getTime();
        retries += 1;
    }
}
