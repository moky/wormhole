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
import chat.dim.type.Data;

/*  https://tools.ietf.org/id/draft-ietf-behave-rfc3489bis-02.txt
 *
 *    10.2.12  XOR-MAPPED-ADDRESS
 *
 *        The XOR-MAPPED-ADDRESS attribute is only present in Binding
 *        Responses.  It provides the same information that is present in the
 *        MAPPED-ADDRESS attribute.  However, the information is encoded by
 *
 *        performing an exclusive or (XOR) operation between the mapped address
 *        and the transaction ID.  Unfortunately, some NAT devices have been
 *        found to rewrite binary encoded IP addresses and ports that are
 *        present in protocol payloads.  This behavior interferes with the
 *        operation of STUN.  By providing the mapped address in an obfuscated
 *        form, STUN can continue to operate through these devices.
 *
 *        The format of the XOR-MAPPED-ADDRESS is:
 *
 *        0                   1                   2                   3
 *        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *        |x x x x x x x x|    Family     |         X-Port                |
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *        |                X-Address (Variable)
 *        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *        The Family represents the IP address family, and is encoded
 *        identically to the Family in MAPPED-ADDRESS.
 *
 *        X-Port is equal to the port in MAPPED-ADDRESS, exclusive or'ed with
 *        most significant 16 bits of the transaction ID.  If the IP address
 *        family is IPv4, X-Address is equal to the IP address in MAPPED-
 *        ADDRESS, exclusive or'ed with the most significant 32 bits of the
 *        transaction ID.  If the IP address family is IPv6, the X-Address is
 *        equal to the IP address in MAPPED-ADDRESS, exclusive or'ed with the
 *        entire 128 bit transaction ID.
 */

public class XorMappedAddressValue2 extends MappedAddressValue {

    public XorMappedAddressValue2(MappedAddressValue value) {
        super(value, value.ip, value.port, value.family);
    }

    public XorMappedAddressValue2(ByteArray data, String ip, int port, byte family) {
        super(data, ip, port, family);
    }

    //
    //  Factories
    //

    public static XorMappedAddressValue2 from(XorMappedAddressValue2 value) {
        return value;
    }

    public static XorMappedAddressValue2 from(MappedAddressValue value) {
        return new XorMappedAddressValue2(value);
    }

    public static XorMappedAddressValue2 from(ByteArray data) {
        MappedAddressValue value = MappedAddressValue.from(data);
        return value == null ? null : new XorMappedAddressValue2(value, value.ip, value.port, value.family);
    }

    // parse value with tag & length
    public static Triad.Value parse(ByteArray data, Triad.Tag tag, Triad.Length length) {
        return from(data);
    }

    public static XorMappedAddressValue2 create(String ip, int port, byte family, ByteArray factor) {
        MappedAddressValue addressValue = MappedAddressValue.create(ip, port, family);
        ByteArray data = xor(addressValue, factor);
        return new XorMappedAddressValue2(data, ip, port, family);
    }

    public static XorMappedAddressValue2 create(String ip, int port, ByteArray factor) {
        return create(ip, port, FAMILY_IPV4, factor);
    }

    public static ByteArray xor(ByteArray addressValue, ByteArray trans_id) {
        int addressLen = addressValue.getSize();
        int factorLen = trans_id.getSize();
        if (addressLen != 8 && addressLen != 20) {
            throw new ArrayIndexOutOfBoundsException("address length error: " + addressLen);
            //return null;
        } else if (factorLen != 16) {
            throw new ArrayIndexOutOfBoundsException("factor should be the \"magic code\" + \"(96-bits) transaction ID\"");
            //return null;
        }
        byte[] address = addressValue.getBuffer();
        byte[] factor = trans_id.getBuffer();
        int addressOffset = addressValue.getOffset();
        int factorOffset = trans_id.getOffset();
        assert address[addressOffset] == 0 : "address data error";
        // create new data buffer
        byte[] array = new byte[addressLen];
        // family
        array[1] = address[addressOffset + 1];
        // X-Port
        array[2] = (byte) (address[addressOffset + 2] ^ factor[factorOffset]);
        array[3] = (byte) (address[addressOffset + 3] ^ factor[factorOffset + 1]);
        // X-Address
        int a_pos = 4;
        int f_pos = 0;
        while (a_pos < addressLen) {
            array[a_pos] = (byte) (address[addressOffset + a_pos] ^ factor[factorOffset + f_pos]);
            a_pos += 1;
            f_pos += 1;
        }
        return new Data(array);
    }
}
