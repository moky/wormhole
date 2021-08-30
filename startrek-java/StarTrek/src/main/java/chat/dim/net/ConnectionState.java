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
package chat.dim.net;

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

import chat.dim.fsm.BaseState;

/**
 *  Connection State
 *  ~~~~~~~~~~~~~~~~
 *
 *  Defined for indicating connection state
 *
 *      DEFAULT     - 'initialized', or sent timeout
 *      CONNECTING  - sent 'PING', waiting for response
 *      CONNECTED   - got response recently
 *      EXPIRED     - long time, needs maintaining (still connected)
 *      MAINTAINING - sent 'PING', waiting for response
 *      ERROR       - long long time no response, connection lost
 */
public class ConnectionState extends BaseState<StateMachine, StateTransition> {

    public static final String DEFAULT     = "default";
    public static final String CONNECTING  = "connecting";
    public static final String CONNECTED   = "connected";
    public static final String MAINTAINING = "maintaining";
    public static final String EXPIRED     = "expired";
    public static final String ERROR       = "error";

    public final String name;

    ConnectionState(String name) {
        super();
        this.name = name;
    }

    @Override
    public boolean equals(Object other) {
        if (other == this) {
            return true;
        } else if (other instanceof ConnectionState) {
            return ((ConnectionState) other).name.equals(name);
        } else if (other instanceof String) {
            return other.equals(name);
        } else {
            return false;
        }
    }
    public boolean equals(String other) {
        return name.equals(other);
    }

    @Override
    public String toString() {
        return name;
    }

    @Override
    public void onEnter(StateMachine ctx) {

    }

    @Override
    public void onExit(StateMachine ctx) {

    }

    @Override
    public void onPause(StateMachine ctx) {

    }

    @Override
    public void onResume(StateMachine ctx) {

    }
}
