/* license: https://mit-license.org
 *
 *  STUN: Session Traversal Utilities for NAT
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
package chat.dim.stun.protocol;

import java.util.Random;

import chat.dim.tlv.Data;
import chat.dim.tlv.MutableData;
import chat.dim.tlv.UInt32Data;

/*  [RFC] https://www.ietf.org/rfc/rfc5389.txt
 *
 *   Transaction ID
 *   ~~~~~~~~~~~~~~
 *
 *   The magic cookie field MUST contain the fixed value 0x2112A442 in
 *   network byte order.  In RFC 3489 [RFC3489], this field was part of
 *   the transaction ID; placing the magic cookie in this location allows
 *   a server to detect if the client will understand certain attributes
 *   that were added in this revised specification.  In addition, it aids
 *   in distinguishing STUN packets from packets of other protocols when
 *   STUN is multiplexed with those other protocols on the same port.
 *
 *   The transaction ID is a 96-bit identifier, used to uniquely identify
 *   STUN transactions.  For request/response transactions, the
 *   transaction ID is chosen by the STUN client for the request and
 *   echoed by the server in the response.  For indications, it is chosen
 *   by the agent sending the indication.  It primarily serves to
 *   correlate requests with responses, though it also plays a small role
 *   in helping to prevent certain types of attacks.  The server also uses
 *   the transaction ID as a key to identify each transaction uniquely
 *   across all clients.  As such, the transaction ID MUST be uniformly
 *   and randomly chosen from the interval 0 .. 2**96-1, and SHOULD be
 *   cryptographically random.  Resends of the same request reuse the same
 *   transaction ID, but the client MUST choose a new transaction ID for
 *   new transactions unless the new request is bit-wise identical to the
 *   previous request and sent from the same transport address to the same
 *   IP address.  Success and error responses MUST carry the same
 *   transaction ID as their corresponding request.  When an agent is
 *   acting as a STUN server and STUN client on the same port, the
 *   transaction IDs in requests sent by the agent have no relationship to
 *   the transaction IDs in requests received by the agent.
 */
public class TransactionID extends Data {

    public TransactionID(Data data) {
        super(data);
    }

    public TransactionID(byte[] bytes) {
        super(bytes);
    }

    //
    //  Factories
    //

    public static TransactionID parse(Data data) {
        int length = data.getLength();
        if (length < 16) {
            //throw new ArrayIndexOutOfBoundsException("Transaction ID length error: " + length);
            return null;
        } else if (length > 16) {
            data = data.slice(0, 16);
        }
        return new TransactionID(data);
    }

    public static synchronized TransactionID create() {
        if (s_low < 0xFFFFFFFFL) {
            s_low += 1;
        } else {
            s_low = 0;
            if (s_middle < 0xFFFFFFFFL) {
                s_middle += 1;
            } else {
                s_middle = 0;
                if (s_high < 0xFFFFFFFFL) {
                    s_high += 1;
                } else {
                    s_high = 0;
                }
            }
        }

        Data mc = MagicCookie;
        Data hi = new UInt32Data(s_high);
        Data mi = new UInt32Data(s_middle);
        Data lo = new UInt32Data(s_low);

        MutableData data = new MutableData(16);
        data.copy(mc, 0, 0, 4);
        data.copy(hi, 0, 4, 4);
        data.copy(mi, 0, 8, 4);
        data.copy(lo, 0, 12, 4);
        return new TransactionID(data);
    }

    // Magic Cookie
    public static UInt32Data MagicCookie = new UInt32Data(0x2112A442);

    private static long s_high;
    private static long s_middle;
    private static long s_low;

    static {
        Random random = new Random();
        s_high = random.nextInt() + 0x80000000L;
        s_middle = random.nextInt() + 0x80000000L;
        s_low = random.nextInt() + 0x80000000L;
    }
}
