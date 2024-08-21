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

import chat.dim.port.Arrival;

public abstract class ArrivalShip implements Arrival {

    /**
     *  Arrival task will be expired after 5 minutes
     *  if still not completed.
     */
    public static long EXPIRES = 300 * 1000; // milliseconds

    // expired time (timestamp in milliseconds)
    private long expired;

    protected ArrivalShip(Date now) {
        super();
        expired = now.getTime() + EXPIRES;
    }
    protected ArrivalShip() {
        this(new Date());
    }

    @Override
    public void touch(Date now) {
        // update expired time
        expired = now.getTime() + EXPIRES;
    }

    @Override
    public Status getStatus(Date now) {
        if (now.getTime() > expired) {
            return Status.EXPIRED;
        } else {
            return Status.ASSEMBLING;
        }
    }
}
