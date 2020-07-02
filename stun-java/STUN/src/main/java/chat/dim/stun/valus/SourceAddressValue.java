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

import chat.dim.tlv.Data;
import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;

/*  11.2.5 SOURCE-ADDRESS
 *
 *        The SOURCE-ADDRESS attribute is present in Binding Responses.  It
 *        indicates the source IP address and port that the server is sending
 *        the response from.  Its syntax is identical to that of MAPPED-
 *        ADDRESS.
 *
 *    (Defined in RFC-3489, removed from RFC-5389)
 */

public class SourceAddressValue extends MappedAddressValue {

    public SourceAddressValue(MappedAddressValue addressValue) {
        super(addressValue);
    }

    public SourceAddressValue(Data data, String ip, int port, byte family) {
        super(data, ip, port, family);
    }

    public SourceAddressValue(String ip, int port, byte family) {
        super(ip, port, family);
    }

    public SourceAddressValue(String ip, int port) {
        super(ip, port);
    }

    public static SourceAddressValue parse(Data data, Tag type, Length length) {
        MappedAddressValue value = MappedAddressValue.parse(data, type, length);
        if (value == null) {
            return null;
        }
        return new SourceAddressValue(value, value.ip, value.port, value.family);
    }
}
