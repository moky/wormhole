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

import java.util.Arrays;

import chat.dim.stun.attributes.AttributeValue;
import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;

/*  Rosenberg, et al.           Standards Track                    [Page 32]
 *
 *  RFC 5389                          STUN                      October 2008
 *
 *
 *   The format of the MAPPED-ADDRESS attribute is:
 *
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |0 0 0 0 0 0 0 0|    Family     |           Port                |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                                                               |
 *      |                 Address (32 bits or 128 bits)                 |
 *      |                                                               |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *               Figure 5: Format of MAPPED-ADDRESS Attribute
 *
 *   The address family can take on the following values:
 *
 *   0x01:IPv4
 *   0x02:IPv6
 *
 *   The first 8 bits of the MAPPED-ADDRESS MUST be set to 0 and MUST be
 *   ignored by receivers.  These bits are present for aligning parameters
 *   on natural 32-bit boundaries.
 *
 *   This attribute is used only by servers for achieving backwards
 *   compatibility with RFC 3489 [RFC3489] clients.
 */

public class MappedAddressValue extends AttributeValue {

    /*  15.1.  MAPPED-ADDRESS
     *
     *    The MAPPED-ADDRESS attribute indicates a reflexive transport address
     *    of the client.  It consists of an 8-bit address family and a 16-bit
     *    port, followed by a fixed-length value representing the IP address.
     *    If the address family is IPv4, the address MUST be 32 bits.  If the
     *    address family is IPv6, the address MUST be 128 bits.  All fields
     *    must be in network byte order.
     */

    public static final byte FAMILY_IPV4 = 0x01;
    public static final byte FAMILY_IPV6 = 0x02;

    public final String ip;
    public final int port;
    public final byte family;

    public MappedAddressValue(byte[] data, String ip, int port, byte family) {
        super(data);
        this.ip = ip;
        this.port = port;
        this.family = family;
    }

    @Override
    public String toString() {
        return "(" + ip + ":" + port + ")";
    }

    static byte[] build(String ip, int port, byte family) {
        byte[] address = IPToBytes(ip, family);
        if (address == null || address.length != 4) {
            throw new ArrayIndexOutOfBoundsException("failed to convert IP: " + ip + ", " + family);
        }
        byte[] data = new byte[8];
        data[0] = '\0';
        data[1] = family;
        data[2] = (byte) ((port & 0xFF00) >> 8);
        data[3] = (byte) (port & 0xFF);
        System.arraycopy(address, 0, data, 4, 4);
        return data;
    }

    public static MappedAddressValue create(String ip, int port, byte family) {
        byte[] data = build(ip, port, family);
        return new MappedAddressValue(data, ip, port, family);
    }

    public static MappedAddressValue create(String ip, int port) {
        return create(ip, port, FAMILY_IPV4);
    }

    private static byte[] IPToBytes(String ip, byte family) {
        if (family == FAMILY_IPV4) {
            // IPv4
            String[] array = ip.split(".");
            if (array.length != 4) {
                throw new IndexOutOfBoundsException("IP error: " + ip);
            }
            byte[] address = new byte[4];
            for (int index = 0; index < 4; ++index) {
                address[index] = (byte) (Integer.parseInt(array[index]) & 0xFF);
            }
            return address;
        } else if (family == FAMILY_IPV6) {
            // TODO: IPv6
            throw new UnsupportedOperationException("IPv6 not support yet");
        } else {
            throw new IllegalArgumentException("unknown address family: " + family);
        }
    }

    private static String bytesToIP(byte[] address, byte family) {
        if (family == FAMILY_IPV4) {
            // IPv4
            if (address.length != 4) {
                throw new IndexOutOfBoundsException("address error: " + Arrays.toString(address));
            }
            String[] array = new String[4];
            for (int index = 0; index < 4; ++index) {
                array[index] = String.valueOf(address[index] & 0xFF);
            }
            return array[0] + "." + array[1] + "." + array[2] + "." + array[3];
        } else if (family == FAMILY_IPV6) {
            // TODO: IPv6
            throw new UnsupportedOperationException("IPv6 not support yet");
        } else {
            throw new IllegalArgumentException("unknown address family: " + family);
        }
    }

    public static MappedAddressValue parse(byte[] data, Tag type, Length length) {
        // check length
        if (length == null || length.value == 0) {
            //throw new ArrayIndexOutOfBoundsException("length error: " + length);
            return null;
        } else {
            int len = length.getIntValue();
            int dataLen = data.length;
            if (len < 0 || len > dataLen) {
                //throw new ArrayIndexOutOfBoundsException("data length error: " + data.length + ", " + length.value);
                return null;
            } else if (len < dataLen) {
                data = slice(data, 0, len);
            }
        }
        // checking
        if (data[0] != 0) {
            return null;
        }
        byte family = data[1];
        // check family
        if ((family == FAMILY_IPV4 && length.value == 8) ||
                (family == FAMILY_IPV6 && length.value == 20)) {
            int port = ((data[2] &0xFF) << 8) | (data[3] & 0xFF);
            String ip = bytesToIP(slice(data, 4), family);
            return new MappedAddressValue(data, ip, port, family);
        } else {
            //throw new IllegalArgumentException("mapped-address error: " + Arrays.toString(data));
            return null;
        }
    }
}
