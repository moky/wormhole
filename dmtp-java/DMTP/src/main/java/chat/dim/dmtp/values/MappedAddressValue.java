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
import chat.dim.dmtp.fields.FieldValue;
import chat.dim.tlv.Data;

/*     Address Values
 *     ~~~~~~~~~~~~~~
 *
 *
 *     The format of the MAPPED-ADDRESS attribute is:
 *
 *        0                   1                   2                   3
 *        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *       |0 0 0 0 0 0 0 0|    Family     |           Port                |
 *       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *       |                                                               |
 *       |                 Address (32 bits or 128 bits)                 |
 *       |                                                               |
 *       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *     The address family can take on the following values:
 *
 *     0x01:IPv4
 *     0x02:IPv6
 *
 *     The first 8 bits of the MAPPED-ADDRESS MUST be set to 0 and MUST be
 *     ignored by receivers.  These bits are present for aligning parameters
 *     on natural 32-bit boundaries.
 */

public class MappedAddressValue extends FieldValue {

    /*  MAPPED-ADDRESS
     *  ~~~~~~~~~~~~~~
     *
     *  The MAPPED-ADDRESS attribute indicates a reflexive transport address
     *  of the client.  It consists of an 8-bit address family and a 16-bit
     *  port, followed by a fixed-length value representing the IP address.
     *  If the address family is IPv4, the address MUST be 32 bits.  If the
     *  address family is IPv6, the address MUST be 128 bits.  All fields
     *  must be in network byte order.
     */

    public static final int FAMILY_IPV4 = 0x01;
    public static final int FAMILY_IPV6 = 0x02;

    public final String ip;
    public final int port;
    public final int family;

    public MappedAddressValue(Data data, String ip, int port, int family) {
        super(data);
        this.ip = ip;
        this.port = port;
        this.family = family;
    }

    public MappedAddressValue(byte[] bytes, String ip, int port, int family) {
        super(bytes);
        this.ip = ip;
        this.port = port;
        this.family = family;
    }

    public MappedAddressValue(String ip, int port, int family) {
        this(build(ip, port, family), ip, port, family);
    }

    public MappedAddressValue(String ip, int port) {
        this(ip, port, FAMILY_IPV4);
    }

    @Override
    public String toString() {
        return "\"" + ip + ":" + port + "\"";
    }

    private static byte[] build(String ip, int port, int family) {
        byte[] ipData = ipToBytes(ip, port, family);
        byte[] data = new byte[4 + ipData.length];
        data[1] = (byte) (family & 0xFF);
        data[2] = (byte) ((port & 0xFF00) >> 8);
        data[3] = (byte) (port & 0xFF);
        System.arraycopy(ipData, 0, data, 4, ipData.length);
        return data;
    }

    private static byte[] ipToBytes(String ip, int port, int family) {
        byte[] data = null;
        switch (family) {
            case FAMILY_IPV4: {
                // IPv4
                String[] array = ip.split("\\.");
                if (array.length == 4) {
                    data = new byte[4];
                    for (int index = 0; index < 4; ++index) {
                        data[index] = (byte) (Integer.parseInt(array[index]) & 0xFF);
                    }
                }
                break;
            }

            case FAMILY_IPV6: {
                // TODO: IPv6
                throw new UnsupportedOperationException("implement me!");
                //break;
            }

            default: {
                throw new IllegalArgumentException("unknown address family: " + family);
                //break;
            }
        }
        return data;
    }

    private static String bytesToIP(byte[] address, int family) {
        String ip = null;
        switch (family) {
            case FAMILY_IPV4: {
                // IPv4
                if (address.length == 4) {
                    StringBuilder sb = new StringBuilder(Integer.toString(address[0] & 0xFF));
                    for (int index = 1; index < 4; ++index) {
                        sb.append(".").append(Integer.toString(address[index] & 0xFF));
                    }
                    ip = sb.toString();
                }
                break;
            }

            case FAMILY_IPV6: {
                // TODO: IPv6
                throw new UnsupportedOperationException("implement me!");
                //break;
            }

            default: {
                throw new IllegalArgumentException("unknown address family: " + family);
                //break;
            }
        }
        return ip;
    }

    public static MappedAddressValue parse(Data data, FieldName type, FieldLength length) {
        if (data.getByte(0) != 0) {
            return null;
        }
        int family = data.getByte(1);
        if (family != FAMILY_IPV4 && family != FAMILY_IPV6) {
            return null;
        }
        int port = ((data.getByte(2) & 0xFF) << 8) | (data.getByte(3) & 0xFF);
        String ip = bytesToIP(data.getBytes(4), family);
        return new MappedAddressValue(data, ip, port, family);
    }
}
