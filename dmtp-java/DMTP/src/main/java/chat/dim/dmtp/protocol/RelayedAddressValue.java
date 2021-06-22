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
package chat.dim.dmtp.protocol;

import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;

public class RelayedAddressValue extends MappedAddressValue {

    /*  RELAYED-ADDRESS
     *  ~~~~~~~~~~~~~~~
     *
     *  The RELAYED-ADDRESS attribute is present in Allocate responses.  It
     *  specifies the address and port that the server allocated to the
     *  client.  It is encoded in the same way as MAPPED-ADDRESS.
     */

    public RelayedAddressValue(MappedAddressValue value) {
        super(value, value.ip, value.port, value.family);
    }

    public RelayedAddressValue(ByteArray data, String ip, int port, byte family) {
        super(data, ip, port, family);
    }

    //
    //  Factories
    //

    public static RelayedAddressValue from(RelayedAddressValue value) {
        return value;
    }

    public static RelayedAddressValue from(MappedAddressValue value) {
        return new RelayedAddressValue(value);
    }

    public static RelayedAddressValue from(ByteArray data) {
        MappedAddressValue value = MappedAddressValue.from(data);
        return value == null ? null : new RelayedAddressValue(value);
    }

    public static RelayedAddressValue create(String ip, int port, byte family) {
        MappedAddressValue value = MappedAddressValue.create(ip, port, family);
        return new RelayedAddressValue(value, ip, port, family);
    }
    public static RelayedAddressValue create(String ip, int port) {
        MappedAddressValue value = MappedAddressValue.create(ip, port);
        return new RelayedAddressValue(value, ip, port, value.family);
    }

    // parse value with tag & length
    public static Triad.Value parse(ByteArray data, Triad.Tag tag, Triad.Length length) {
        return from(data);
    }
}
