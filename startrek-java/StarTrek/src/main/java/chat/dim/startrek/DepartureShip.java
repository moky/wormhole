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

import chat.dim.port.Departure;

public abstract class DepartureShip implements Departure {

    /**
     *  Departure task will be expired after 2 minutes if no response received.
     */
    public static long EXPIRES = 120 * 1000; // milliseconds

    /**
     *  Departure task will be retried 2 times if response timeout
     */
    public static int RETRIES = 2;

    // if (max_tries == -1),
    // means this ship well be sent only once
    // and no need to wait for response.
    public static final int DISPOSABLE = -1;

    // expired time (timestamp in milliseconds)
    private long expired;

    // tries:
    //    -1, this ship needs no response, so it will be sent out
    //        and removed immediately;
    //     0, this ship was sent and now is waiting for response,
    //        it should be removed after expired;
    //    >0, this task needs retry and waiting for response,
    //        don't remove it now.
    private int tries;

    // task priority, smaller is faster
    private final int priority;

    protected DepartureShip(int prior, int maxTries) {
        super();
        assert maxTries != 0 : "max tries should not be 0";
        priority = prior;
        expired = 0;
        tries = maxTries;
    }
    protected DepartureShip() {
        this(0, 1 + RETRIES);
    }

    @Override
    public int getPriority() {
        return priority;
    }

    //
    //  task states
    //

    @Override
    public boolean isNew() {
        return expired == 0;
    }

    @Override
    public boolean isDisposable() {
        return tries <= 0;  // -1
    }

    @Override
    public boolean isTimeout(long now) {
        return tries > 0 && now > expired;
    }

    @Override
    public boolean isFailed(long now) {
        return tries == 0 && now > expired;
    }

    @Override
    public void touch(long now) {
        assert tries > 0 : "touch error, tries=" + tries;
        // update retried time
        expired = now + EXPIRES;
        // decrease counter
        --tries;
    }
}
