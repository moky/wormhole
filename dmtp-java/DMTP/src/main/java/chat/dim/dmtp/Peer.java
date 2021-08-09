/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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
package chat.dim.dmtp;

import java.net.SocketAddress;

import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;
import chat.dim.net.Connection;

/*    Topology:
 *
 *        +-----------------------------------------------+
 *        |                      APP                      |
 *        |                 (Peer Handler)                |
 *        +-----------------------------------------------+
 *                            |       A
 *                            |       |
 *                            V       |
 *        +---+--------+----------------------------------+
 *        |   |  Pool  |                                  |        pool:
 *        |   +--------+         Peer        +--------+   |          -> departures
 *        |                (Hub Listener)    | Filter |   |          -> arrivals
 *        +----------------------------------+--------+---+          -> assembling
 *                            |       A
 *                            |       |
 *                            V       |
 *        +-----------------------------------------------+
 *        |                      HUB                      |
 *        +-----------------------------------------------+
 */

//public interface Peer extends Runnable {
//
//    SocketAddress getLocalAddress();
//
//    Connection getConnection(SocketAddress remote);
//
//    void connect(SocketAddress remote);
//    void disconnect(SocketAddress remote);
//
//    void terminate();
//
//    //
//    //  Send
//    //
//
//    /**
//     *  Send message to destination address
//     *
//     * @param msg         - message data
//     * @param destination - remote address
//     * @return false on error
//     */
//    boolean sendMessage(Message msg, SocketAddress destination);
//
//    /**
//     *  Send command to destination address
//     *
//     * @param cmd         - command data
//     * @param destination - remote address
//     * @return false on error
//     */
//    boolean sendCommand(Command cmd, SocketAddress destination);
//
//    //
//    //  Process
//    //
//
//    /**
//     *  Process received message from remote source address
//     *
//     * @param msg    - message info
//     * @param source - remote address
//     * @return false on error
//     */
//    boolean processMessage(Message msg, SocketAddress source);
//
//    /**
//     *  Process received command from remote source address
//     *
//     * @param cmd    - command info
//     * @param source - remote address
//     * @return false on error
//     */
//    boolean processCommand(Command cmd, SocketAddress source);
//}
