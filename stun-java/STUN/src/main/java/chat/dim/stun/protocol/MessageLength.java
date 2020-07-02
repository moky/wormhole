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

import chat.dim.tlv.Data;
import chat.dim.tlv.UInt16Data;

public class MessageLength extends UInt16Data {

    public MessageLength(UInt16Data data) {
        super(data);
    }

    public MessageLength(Data data, int value) {
        super(data, value);
    }

    public MessageLength(byte[] bytes, int value) {
        super(bytes, value);
    }

    public MessageLength(int value) {
        this(bytesFromLong(value, 2), value);
    }

    //
    //  Factory
    //

    public static MessageLength parse(Data data) {
        if (data.getLength() < 2 || (data.getByte(0) & 0x03) != 0) {
            // format: xxxx xxxx, xxxx, xx00
            return null;
        } else if (data.getLength() > 2) {
            data = data.slice(0, 2);
        }
        int value = data.getUInt16Value(0);
        return new MessageLength(data, value);
    }
}
