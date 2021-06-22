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

import chat.dim.tlv.RawValue;
import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;
import chat.dim.type.MutableData;

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

public class MappedAddressValue extends RawValue {

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

    public static final byte FAMILY_IPV4 = 0x01;
    public static final byte FAMILY_IPV6 = 0x02;

    public final String ip;
    public final int port;
    public final byte family;

    public MappedAddressValue(ByteArray data, String ip, int port, byte family) {
        super(data);
        this.ip = ip;
        this.port = port;
        this.family = family;
    }

    @Override
    public String toString() {
        return "\"" + ip + ":" + port + "\"";
    }

    //
    //  Factories
    //

    public static MappedAddressValue from(MappedAddressValue value) {
        return value;
    }

    public static MappedAddressValue from(ByteArray data) {
        // checking
        if (data.getByte(0) != 0) {
            return null;
        }
        byte family = data.getByte(1);
        if (family == FAMILY_IPV4) {
            // IPv4
            if (data.getSize() == 8) {
                int port = ((data.getByte(2) & 0xFF) << 8) | (data.getByte(3) & 0xFF);
                String ip = dataToIPv4(data.slice(4));
                return new MappedAddressValue(data, ip, port, family);
            }
        }
        return null;
    }

    public static MappedAddressValue from(String ip, int port, byte family) {
        ByteArray data = getData(ip, port, family);
        return new MappedAddressValue(data, ip, port, family);
    }
    public static MappedAddressValue from(String ip, int port) {
        ByteArray data = getData(ip, port, FAMILY_IPV4);
        return new MappedAddressValue(data, ip, port, FAMILY_IPV4);
    }

    // parse value with tag & length
    public static Triad.Value parse(ByteArray data, Triad.Tag tag, Triad.Length length) {
        return from(data);
    }

    //
    //  Converting
    //

    private static ByteArray getData(String ip, int port, byte family) {
        ByteArray address = null;
        if (family == FAMILY_IPV4) {
            // IPv4
            address = dataFromIPv4(ip);
        }
        assert address != null : "failed to convert IP: " + ip + ", " + family;
        MutableData data = new MutableData(8);
        data.append((byte) 0);
        data.append(family);
        data.append((byte) ((port & 0xFF00) >> 8));
        data.append((byte) (port & 0xFF));
        data.append(address);
        return data;
    }

    private static ByteArray dataFromIPv4(String ip) {
        String[] array = ip.split("\\.");
        if (array.length != 4) {
            throw new IndexOutOfBoundsException("IP error: " + ip);
        }
        MutableData address = new MutableData(4);
        for (int index = 0; index < 4; ++index) {
            address.append((byte) Integer.parseInt(array[index]));
        }
        return address;
    }

    private static String dataToIPv4(ByteArray address) {
        if (address.getSize() != 4) {
            throw new IndexOutOfBoundsException("address error: " + address);
        }
        String[] array = new String[4];
        for (int index = 0; index < 4; ++index) {
            array[index] = String.valueOf(address.getByte(index) & 0xFF);
        }
        return array[0] + "." + array[1] + "." + array[2] + "." + array[3];
    }
}
