/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.net;

/*
 *  Architecture:
 *
 *                 Connection        Connection      Connection
 *                 Delegate          Delegate        Delegate
 *                     ^                 ^               ^
 *                     :                 :               :
 *        ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
 *                     :                 :               :
 *          +===+------V-----+====+------V-----+===+-----V------+===+
 *          ||  | connection |    | connection |   | connection |  ||
 *          ||  +------------+    +------------+   +------------+  ||
 *          ||          :                :               :         ||
 *          ||          :      HUB       :...............:         ||
 *          ||          :                        :                 ||
 *          ||     +-----------+           +-----------+           ||
 *          ||     |  channel  |           |  channel  |           ||
 *          +======+-----------+===========+-----------+============+
 *                 |  socket   |           |  socket   |
 *                 +-----^-----+           +-----^-----+
 *                       : (TCP)                 : (UDP)
 *                       :               ........:........
 *                       :               :               :
 *        ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
 *                       :               :               :
 *                       V               V               V
 *                  Remote Peer     Remote Peer     Remote Peer
 */

import java.net.DatagramSocket;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.Set;

import chat.dim.skywalker.Processor;

/**
 *  Connections & Channels Container
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public interface Hub extends Processor {

    /**
     *  Get opened channel with direction (remote, local)
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on socket closed
     */
    Channel getChannel(SocketAddress remote, SocketAddress local);

    /**
     *  Close socket channel
     *
     * @param channel - socket channel
     */
    void closeChannel(Channel channel);

    /**
     *  Get connection with direction (remote, local)
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on connection not found
     */
    Connection getConnection(SocketAddress remote, SocketAddress local);

    /**
     *  Close connection
     *
     * @param connection - closing connection
     */
    void closeConnection(Connection connection);

    //
    //  Local Address
    //

    static Set<NetworkInterface> getNetworkInterfaces() throws SocketException {
        Set<NetworkInterface> interfaces = new HashSet<>();
        Enumeration<NetworkInterface> e = NetworkInterface.getNetworkInterfaces();
        while (e.hasMoreElements()) {
            interfaces.add(e.nextElement());
        }
        return interfaces;
    }
    static Set<InetAddress> getInetAddresses(NetworkInterface ni) {
        Set<InetAddress> addresses = new HashSet<>();
        Enumeration<InetAddress> e = ni.getInetAddresses();
        InetAddress ip;
        while (e.hasMoreElements()) {
            ip = e.nextElement();
            if (ip instanceof Inet4Address && !ip.isLoopbackAddress()) {
                addresses.add(ip);
            }
        }
        return addresses;
    }
    static Set<InetAddress> getInetAddresses(Set<NetworkInterface> interfaces) {
        Set<InetAddress> addresses = new HashSet<>();
        for (NetworkInterface ni : interfaces) {
            addresses.addAll(getInetAddresses(ni));
        }
        return addresses;
    }

    static InetAddress getLocalAddress() throws SocketException {
        Set<InetAddress> addresses = getInetAddresses(getNetworkInterfaces());
        if (addresses.size() > 0) {
            return addresses.iterator().next();
        }
        try (DatagramSocket socket = new DatagramSocket()) {
            SocketAddress remote = new InetSocketAddress("8.8.8.8", 8888);
            socket.connect(remote);
            return socket.getLocalAddress();
        }
    }
    static String getLocalAddressString() throws SocketException {
        InetAddress address = getLocalAddress();
        return address == null ? null : address.getHostAddress();
    }
}
