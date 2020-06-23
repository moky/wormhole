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

/* Rosenberg, et al.           Standards Track                    [Page 33]
 *
 * RFC 5389                          STUN                      October 2008
 *
 *   The format of the XOR-MAPPED-ADDRESS is:
 *
 *      0                   1                   2                   3
 *      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *     |x x x x x x x x|    Family     |         X-Port                |
 *     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *     |                X-Address (Variable)
 *     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *             Figure 6: Format of XOR-MAPPED-ADDRESS Attribute
 *
 *   The Family represents the IP address family, and is encoded
 *   identically to the Family in MAPPED-ADDRESS.
 */

public class XorMappedAddressValue extends MappedAddressValue {

    /*  15.2.  XOR-MAPPED-ADDRESS
     *
     *    The XOR-MAPPED-ADDRESS attribute is identical to the MAPPED-ADDRESS
     *    attribute, except that the reflexive transport address is obfuscated
     *    through the XOR function.
     *
     *    X-Port is computed by taking the mapped port in host byte order,
     *    XOR'ing it with the most significant 16 bits of the magic cookie, and
     *    then the converting the result to network byte order.  If the IP
     *    address family is IPv4, X-Address is computed by taking the mapped IP
     *    address in host byte order, XOR'ing it with the magic cookie, and
     *    converting the result to network byte order.  If the IP address
     *    family is IPv6, X-Address is computed by taking the mapped IP address
     *    in host byte order, XOR'ing it with the concatenation of the magic
     *    cookie and the 96-bit transaction ID, and converting the result to
     *    network byte order.
     *
     *    The rules for encoding and processing the first 8 bits of the
     *    attribute's value, the rules for handling multiple occurrences of the
     *    attribute, and the rules for processing address families are the same
     *    as for MAPPED-ADDRESS.
     *
     *    Note: XOR-MAPPED-ADDRESS and MAPPED-ADDRESS differ only in their
     *    encoding of the transport address.  The former encodes the transport
     *    address by exclusive-or'ing it with the magic cookie.  The latter
     *    encodes it directly in binary.  RFC 3489 originally specified only
     *    MAPPED-ADDRESS.  However, deployment experience found that some NATs
     *    rewrite the 32-bit binary payloads containing the NAT's public IP
     *    address, such as STUN's MAPPED-ADDRESS attribute, in the well-meaning
     *    but misguided attempt at providing a generic ALG function.  Such
     *    behavior interferes with the operation of STUN and also causes
     *    failure of STUN's message-integrity checking.
     */

    public XorMappedAddressValue(byte[] data, String ip, int port, byte family) {
        super(data, ip, port, family);
    }

    public static XorMappedAddressValue create(String ip, int port, byte family, byte[] factor) {
        byte[] data = build(ip, port, family);
        data = xor(data, factor);
        return new XorMappedAddressValue(data, ip, port, family);
    }

    public static XorMappedAddressValue create(String ip, int port, byte[] factor) {
        return create(ip, port, FAMILY_IPV4, factor);
    }

    public static byte[] xor(byte[] data, byte[] factor) {
        if (data.length != 8 && data.length != 20) {
            throw new ArrayIndexOutOfBoundsException("address length error: " + data.length);
            //return null;
        } else if (factor.length != 16) {
            throw new ArrayIndexOutOfBoundsException("factor should be the \"magic code\" + \"(96-bits) transaction ID\"");
            //return null;
        }
        assert data[0] == 0 : "address data error";
        byte[] array = new byte[data.length];
        array[0] = data[0];
        array[1] = data[1];
        // X-Port
        array[2] = (byte) (data[2] ^ factor[1]);
        array[3] = (byte) (data[3] ^ factor[0]);
        // X-Address
        int a_pos = data.length - 1;
        int f_pos = 0;
        while (a_pos >= 4) {
            array[a_pos] = (byte) (data[a_pos] & factor[f_pos]);
            a_pos -= 1;
            f_pos += 1;
        }
        return array;
    }

    public static XorMappedAddressValue parse(byte[] data, Tag type, Length length) {
        MappedAddressValue value = MappedAddressValue.parse(data, type, length);
        if (value == null) {
            return null;
        }
        return new XorMappedAddressValue(value.data, value.ip, value.port, value.family);
    }

    static {
        //register(AttributeType.XorMappedAddress, XorMappedAddressValue.class);
    }
}
