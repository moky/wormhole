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
package chat.dim.port;

import java.util.Date;

/**
 *  Star Ship
 *  ~~~~~~~~~
 *
 *  Container carrying data package
 */
public interface Ship {

    /**
     *  Get ID for this Ship
     *
     * @return SN
     */
    Object getSN();

    /**
     *  Update sent time
     *
     * @param now - current time
     */
    void touch(Date now);

    /**
     *  Check ship state
     *
     * @param now - current time
     * @return current status
     */
    Status getStatus(Date now);

    /**
     *  Ship Status
     *  ~~~~~~~~~~~
     */
    enum Status {
        //
        //  Departure Status
        //
        NEW        (0x00),  // not try yet
        WAITING    (0x01),  // sent, waiting for responses
        TIMEOUT    (0x02),  // waiting to send again
        DONE       (0x03),  // all fragments responded (or no need respond)
        FAILED     (0x04),  // tried 3 times and missed response(s)

        //
        //  Arrival Status
        //
        ASSEMBLING (0x10),  // waiting for more fragments
        EXPIRED    (0x11);  // failed to received all fragments

        public final int value;

        Status(int state) {
            value = state;
        }
    }

}
