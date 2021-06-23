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
package chat.dim.stun.valus;

import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;

/*  11.2.2 RESPONSE-ADDRESS
 *
 *        The RESPONSE-ADDRESS attribute indicates where the response to a
 *        Binding Request should be sent.  Its syntax is identical to MAPPED-
 *        ADDRESS.
 *
 *    (Defined in RFC-3489, removed from RFC-5389)
 */

public class ResponseAddressValue extends MappedAddressValue {

    public ResponseAddressValue(ByteArray data, String ip, int port, byte family) {
        super(data, ip, port, family);
    }

    //
    //  Factories
    //

    public static ResponseAddressValue from(ResponseAddressValue value) {
        return value;
    }

    public static ResponseAddressValue from(MappedAddressValue value) {
        return new ResponseAddressValue(value, value.ip, value.port, value.family);
    }

    public static ResponseAddressValue from(ByteArray data) {
        MappedAddressValue value = MappedAddressValue.from(data);
        return value == null ? null : from(value);
    }

    public static ResponseAddressValue create(String ip, int port, byte family) {
        return from(MappedAddressValue.create(ip, port, family));
    }
    public static ResponseAddressValue create(String ip, int port) {
        return from(MappedAddressValue.create(ip, port));
    }

    // parse value with tag & length
    public static Triad.Value parse(ByteArray data, Triad.Tag tag, Triad.Length length) {
        return from(data);
    }
}
