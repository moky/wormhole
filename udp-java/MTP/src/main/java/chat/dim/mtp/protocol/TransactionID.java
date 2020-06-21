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
package chat.dim.mtp.protocol;

import java.util.Random;

import chat.dim.tlv.Data;
import chat.dim.tlv.UInt32Data;

public class TransactionID extends Data {

    public TransactionID(byte[] data) {
        super(data);
    }

    public static TransactionID parse(byte[] data) {
        int length = data.length;
        if (length < 8) {
            throw new ArrayIndexOutOfBoundsException("Transaction ID length error: " + length);
        } else if (length > 8) {
            data = slice(data, 0, 8);
        }
        return new TransactionID(data);
    }

    //
    //  Factory
    //

    public static synchronized TransactionID create() {
        if (s_low < 0xFFFFFFFF) {
            s_low += 1;
        } else {
            s_low = 0;
            if (s_high < 0xFFFFFFFF) {
                s_high += 1;
            } else {
                s_high = 0;
            }
        }
        byte[] hi = UInt32Data.intToBytes((int) s_high, 4);
        byte[] lo = UInt32Data.intToBytes((int) s_low, 4);
        byte[] data = concat(hi, lo);
        return new TransactionID(data);
    }

    private static long s_high;
    private static long s_low;

    static {
        Random random = new Random();
        s_high = random.nextInt();
        s_low = random.nextInt();
    }
}
