/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
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
package chat.dim.tlv;

import java.util.List;

import chat.dim.type.ByteArray;
import chat.dim.type.IntegerData;

/*
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |         Type                  |            Length             |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Value (variable)                ....
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

public interface Triad<T extends Triad.Tag, L extends Triad.Length, V extends Triad.Value> extends ByteArray {

    T getTag();
    L getLength();
    V getValue();

    interface Tag extends ByteArray {
        /**
         *  Tag Parser
         *  ~~~~~~~~~~
         */
        interface Parser<T> {
            T parseTag(ByteArray data);
        }
    }
    interface Length extends ByteArray, IntegerData {
        /**
         *  Length Parser
         *  ~~~~~~~~~~~~~
         */
        interface Parser<T, L> {
            L parseLength(ByteArray data, T tag);
        }
    }
    interface Value extends ByteArray {
        /**
         *  Value Parser
         *  ~~~~~~~~~~~~
         */
        interface Parser<T, L, V> {
            V parseValue(ByteArray data, T tag, L length);
        }
    }

    /**
     *  Tag-Length-Value Parser
     *  ~~~~~~~~~~~~~~~~~~~~~~~
     */
    interface Parser<A> {

        A parseTriad(ByteArray data);

        /**
         *  Parse all TLV triads
         *
         * @param data - data received
         * @return TLV list
         */
        List<A> parseTriads(ByteArray data);
    }
}
