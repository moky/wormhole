/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
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
package chat.dim.mtp;

import java.net.SocketAddress;
import java.util.List;

import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;
import chat.dim.type.Data;

public interface PeerHandler {

    //
    //  Callbacks
    //

    /**
     *  Callback for send command success
     *
     * @param sn          - transaction ID
     * @param destination - remote IP and port
     * @param source      - local IP and port
     */
    void onSendCommandSuccess(TransactionID sn, SocketAddress destination, SocketAddress source);

    /**
     *  Callback for send command failed
     *
     * @param sn          - transaction ID
     * @param destination - remote IP and port
     * @param source      - local IP and port
     */
    void onSendCommandTimeout(TransactionID sn, SocketAddress destination, SocketAddress source);

    /**
     *  Callback for send message success
     *
     * @param sn          - transaction ID
     * @param destination - remote IP and port
     * @param source      - local IP and port
     */
    void onSendMessageSuccess(TransactionID sn, SocketAddress destination, SocketAddress source);


    /**
     *  Callback for send message failed
     *
     * @param sn          - transaction ID
     * @param destination - remote IP and port
     * @param source      - local IP and port
     */
    void onSendMessageTimeout(TransactionID sn, SocketAddress destination, SocketAddress source);

    //
    //  Received
    //

    /**
     *  Received command data from source address.
     *
     * @param cmd         - command data received
     * @param source      - remote IP and port
     * @param destination - local IP and port
     * @return false on error
     */
    boolean onReceivedCommand(Data cmd, SocketAddress source, SocketAddress destination);

    /**
     *  Received command data from source address.
     *
     * @param msg         - message data received
     * @param source      - remote IP and port
     * @param destination - local IP and port
     * @return false on error
     */
    boolean onReceivedMessage(Data msg, SocketAddress source, SocketAddress destination);

    /**
     *  Received error data from source address.
     *
     * @param data        - error data received
     * @param source      - remote IP and port
     * @param destination - local IP and port
     */
    void onReceivedError(Data data, SocketAddress source, SocketAddress destination);

    //
    //  Fragments
    //

    /**
     *  Check message fragment from the source address, if too many incomplete tasks
     *  from the same address, return False to reject it to avoid 'DDoS' attack.
     *
     * @param fragment    - message fragment
     * @param source      - remote IP and port
     * @param destination - local IP and port
     * @return false on error
     */
    boolean checkFragment(Package fragment, SocketAddress source, SocketAddress destination);

    /**
     *  Recycle incomplete message fragments from source address.
     *  (Override for resuming the transaction)
     *
     * @param fragments   - packages list
     * @param source      - remote IP and port
     * @param destination - local IP and port
     */
    void recycleFragments(List<Package> fragments, SocketAddress source, SocketAddress destination);
}
