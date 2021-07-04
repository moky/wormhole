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

import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.tlv.Value;
import chat.dim.type.ByteArray;

/**  11.2.3  CHANGED-ADDRESS
 *
 *        The CHANGED-ADDRESS attribute indicates the IP address and port where
 *        responses would have been sent from if the "change IP" and "change
 *        port" flags had been set in the CHANGE-REQUEST attribute of the
 *        Binding Request.  The attribute is always present in a Binding
 *        Response, independent of the value of the flags.  Its syntax is
 *        identical to MAPPED-ADDRESS.
 *
 *    (Defined in RFC-3489, removed from RFC-5389)
 */
public class ChangedAddressValue extends MappedAddressValue {

    public ChangedAddressValue(ByteArray data, String ip, int port, byte family) {
        super(data, ip, port, family);
    }

    //
    //  Factories
    //

    public static ChangedAddressValue from(ChangedAddressValue value) {
        return value;
    }

    public static ChangedAddressValue from(MappedAddressValue value) {
        return new ChangedAddressValue(value, value.ip, value.port, value.family);
    }

    public static ChangedAddressValue from(ByteArray data) {
        MappedAddressValue value = MappedAddressValue.from(data);
        return value == null ? null : from(value);
    }

    public static ChangedAddressValue create(String ip, int port, byte family) {
        return from(MappedAddressValue.create(ip, port, family));
    }
    public static ChangedAddressValue create(String ip, int port) {
        return from(MappedAddressValue.create(ip, port));
    }

    // parse value with tag & length
    public static Value parse(ByteArray data, Tag tag, Length length) {
        return from(data);
    }
}
