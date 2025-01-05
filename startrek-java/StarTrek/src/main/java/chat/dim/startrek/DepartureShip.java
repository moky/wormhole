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

import java.util.Date;
import java.util.List;

import chat.dim.port.Departure;
import chat.dim.type.Duration;

public abstract class DepartureShip implements Departure {

    /**
     *  Departure task will be expired after 2 minutes
     *  if no response received.
     */
    public static Duration EXPIRES = Duration.ofMinutes(2);

    /**
     *  Important departure task will be retried 2 times
     *  if response timeout.
     */
    public static int RETRIES = 2;

    // expired time
    private Date expired;

    // how many times to try sending
    private int tries;

    // task priority, smaller is faster
    private final int priority;

    protected DepartureShip(int prior, int maxTries) {
        super();
        assert maxTries != 0 : "max tries should not be 0";
        tries = maxTries;
        priority = prior;
        expired = null;
    }
    protected DepartureShip() {
        super();
        tries = 1 + RETRIES;
        priority = 0;
        expired = null;
    }

    @Override
    public void touch(Date now) {
        assert tries > 0 : "touch error, tries=" + tries;
        // decrease counter
        --tries;
        // update retried time
        expired = EXPIRES.addTo(now);
    }

    @Override
    public Status getStatus(Date now) {
        Date exp = expired;
        List<byte[]> fragments = getFragments();
        if (fragments == null || fragments.size() == 0) {
            return Status.DONE;
        } else if (exp == null) {
            return Status.NEW;
        //} else if (!isImportant()) {
        //    return Status.DONE;
        } else if (now.before(exp)) {
            return Status.WAITING;
        } else if (tries > 0) {
            return Status.TIMEOUT;
        } else {
            return Status.FAILED;
        }
    }

    @Override
    public int getPriority() {
        return priority;
    }

}
