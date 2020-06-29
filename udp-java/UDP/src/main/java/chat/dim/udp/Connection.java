/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.udp;

import java.net.SocketAddress;
import java.util.Date;

/*    Finite States:
 *
 *             //===============\\          (Sent)          //==============\\
 *             ||               || -----------------------> ||              ||
 *             ||    Default    ||                          ||  Connecting  ||
 *             || (Not Connect) || <----------------------- ||              ||
 *             \\===============//         (Timeout)        \\==============//
 *                                                               |       |
 *             //===============\\                               |       |
 *             ||               || <-----------------------------+       |
 *             ||     Error     ||          (Error)                 (Received)
 *             ||               || <-----------------------------+       |
 *             \\===============//                               |       |
 *                 A       A                                     |       |
 *                 |       |            //===========\\          |       |
 *                 (Error) +----------- ||           ||          |       |
 *                 |                    ||  Expired  || <--------+       |
 *                 |       +----------> ||           ||          |       |
 *                 |       |            \\===========//          |       |
 *                 |       (Timeout)           |         (Timeout)       |
 *                 |       |                   |                 |       V
 *             //===============\\     (Sent)  |            //==============\\
 *             ||               || <-----------+            ||              ||
 *             ||  Maintaining  ||                          ||  Connected   ||
 *             ||               || -----------------------> ||              ||
 *             \\===============//       (Received)         \\==============//
 */
public class Connection {

    public final SocketAddress remoteAddress;
    public final SocketAddress localAddress;

    // connection status
    private ConnectionStatus status = ConnectionStatus.Default;
    private long lastSentTime = 0;
    private long lastReceivedTime = 0;

    public static long EXPIRES = 28 * 1000;  // milliseconds

    public Connection(SocketAddress remoteAddress, SocketAddress localAddress) {
        super();
        this.localAddress = localAddress;
        this.remoteAddress = remoteAddress;
        // initialize times to expired
        long now = (new Date()).getTime();
        lastSentTime = now - EXPIRES - 1;
        lastReceivedTime = now - EXPIRES - 1;
    }

    public boolean isConnected() {
        return getStatus().isConnected();
    }

    public boolean isExpired() {
        return getStatus().isExpired();
    }

    public boolean isError() {
        return getStatus().isError();
    }

    public ConnectionStatus getStatus() {
        Date now = new Date();
        return getStatus(now.getTime());
    }

    /**
     *  Get connection status
     *
     * @param now - timestamp in milliseconds
     * @return new status
     */
    public ConnectionStatus getStatus(long now) {
        // pre-checks
        if (now < lastReceivedTime + EXPIRES) {
            // received response recently
            if (now < lastSentTime + EXPIRES) {
                // sent recently, set status = 'connected'
                status = ConnectionStatus.Connected;
            } else {
                // long time no sending, set status = 'maintain_expired'
                status = ConnectionStatus.Expired;
            }
            return status;
        }
        if (!status.equals(ConnectionStatus.Default)) {
            // any status except 'initialized'
            if (now > lastReceivedTime + (EXPIRES << 2)) {
                // long long time no response, set status = 'error'
                status = ConnectionStatus.Error;
                return status;
            }
        }
        // check with current status
        switch (status) {
            case Default: {
                if (now < lastSentTime + EXPIRES) {
                    // sent recently, change status to 'connecting'
                    status = ConnectionStatus.Connecting;
                }
                break;
            }

            case Connecting: {
                if (now > lastSentTime + EXPIRES) {
                    // long time no sending, change status to 'not_connect'
                    status = ConnectionStatus.Default;
                }
                break;
            }

            case Connected: {
                if (now > lastReceivedTime + EXPIRES) {
                    // long time no response, needs maintaining
                    if (now < lastSentTime + EXPIRES) {
                        // sent recently, change status to 'maintaining'
                        status = ConnectionStatus.Maintaining;
                    } else {
                        // long time no sending, change status to 'maintain_expired'
                        status = ConnectionStatus.Expired;
                    }
                }
                break;
            }

            case Expired: {
                if (now < lastSentTime + EXPIRES) {
                    // sent recently, change status to 'maintaining'
                    status = ConnectionStatus.Maintaining;
                }
                break;
            }

            case Maintaining: {
                if (now > lastSentTime + EXPIRES) {
                    // long time no sending, change status to 'maintain_expired'
                    status = ConnectionStatus.Expired;
                }
                break;
            }

            default: {
                break;
            }
        }
        return status;
    }

    /**
     *  Update last sent time
     *
     * @param now - milliseconds
     * @return new status
     */
    public ConnectionStatus updateSentTime(long now) {
        // update last sent time
        lastSentTime = now;
        // update and return new status
        return getStatus(now);
    }

    /**
     *  Update last received time
     *
     * @param now - milliseconds
     * @return new status
     */
    public ConnectionStatus updateReceivedTime(long now) {
        // update last received time
        lastReceivedTime = now;
        // update and return new status
        return getStatus(now);
    }
}
