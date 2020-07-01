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
package chat.dim.dmtp.values;

import chat.dim.dmtp.fields.FieldLength;
import chat.dim.dmtp.fields.FieldName;

public class RelayedAddressValue extends MappedAddressValue {

    /*  RELAYED-ADDRESS
     *  ~~~~~~~~~~~~~~~
     *
     *  The RELAYED-ADDRESS attribute is present in Allocate responses.  It
     *  specifies the address and port that the server allocated to the
     *  client.  It is encoded in the same way as MAPPED-ADDRESS.
     */

    public RelayedAddressValue(byte[] data, String ip, int port, int family) {
        super(data, ip, port, family);
    }

    public RelayedAddressValue(String ip, int port, int family) {
        super(ip, port, family);
    }

    public RelayedAddressValue(String ip, int port) {
        super(ip, port);
    }

    public static RelayedAddressValue parse(byte[] data, FieldName type, FieldLength length) {
        MappedAddressValue value = MappedAddressValue.parse(data, type, length);
        if (value == null) {
            return null;
        }
        return new RelayedAddressValue(data, value.ip, value.port, value.family);
    }
}
