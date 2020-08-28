/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
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
package chat.dim.tcp;

/*
 *    Finite States:
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

/*
 *  @enum ConnectionStatus
 *
 *  @abstract Defined for indicating connection status
 *
 *  @discussion connection status.
 *
 *      Default     - 'initialized', or sent timeout
 *      Connecting  - sent 'PING', waiting for response
 *      Connected   - got response recently
 *      Expired     - long time, needs maintaining (still connected)
 *      Maintaining - sent 'PING', waiting for response
 *      Error       - long long time no response, connection lost
 *
 *  Bits:
 *      0000 0001 - indicates sent something just now
 *      0000 0010 - indicates sent something not too long ago
 *
 *      0001 0000 - indicates received something just now
 *      0010 0000 - indicates received something not too long ago
 *
 *      (All above are just some advices to help choosing numbers :P)
 */
public enum ConnectionStatus {

    Default     (0x00),  // 0000 0000
    Connecting  (0x01),  // 0000 0001, sent just now
    Connected   (0x11),  // 0001 0001, received just now
    Maintaining (0x21),  // 0010 0001, received not long ago, sent just now
    Expired     (0x22),  // 0010 0010, received not long ago, needs sending
    Error       (0x03);  // 0000 0011, long time no response

    public final int value;

    ConnectionStatus(int value) {
        this.value = value;
    }

    public boolean isConnected() {
        return isConnected(value);
    }

    public boolean isExpired() {
        return isExpired(value);
    }

    public boolean isError() {
        return isError(value);
    }

    public static boolean isConnected(int status) {
        return (status & 0x30) != 0;  // received something not long ago
    }

    public static boolean isExpired(int status) {
        return (status & 0x01) == 0;  // sent nothing in a period
    }

    public static boolean isError(int status) {
        return status == Error.value;  // sent for a long time, but received nothing
    }
}
