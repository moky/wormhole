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
import chat.dim.type.Duration;

public abstract class ArrivalShip implements Arrival {

    /**
     *  Arrival task will be expired after 5 minutes
     *  if still not completed.
     */
    public static Duration EXPIRES = Duration.ofMinutes(5);

    // expired time (timestamp in milliseconds)
    private Date expired;

    protected ArrivalShip(Date now) {
        super();
        assert now != null : "date time error";
        expired = EXPIRES.addTo(now);
    }
    protected ArrivalShip() {
        super();
        expired = EXPIRES.addTo(new Date());
    }

    @Override
    public void touch(Date now) {
        assert now != null : "date time error";
        // update expired time
        expired = EXPIRES.addTo(now);
    }

    @Override
    public Status getStatus(Date now) {
        assert now != null : "date time error";
        if (now.after(expired)) {
            return Status.EXPIRED;
        } else {
            return Status.ASSEMBLING;
        }
    }

}
