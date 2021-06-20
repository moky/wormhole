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
package chat.dim.stun;

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Map;

import chat.dim.stun.attributes.Attribute;
import chat.dim.stun.protocol.Package;
import chat.dim.type.ByteArray;
import chat.dim.udp.Cargo;
import chat.dim.udp.Hub;

/**
 *  Session Traversal Utilities for NAT
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 *  Common interfaces for STUN Server or Client nodes
 */

public abstract class Node {

    /*  11.2.5 SOURCE-ADDRESS
     *
     *        The SOURCE-ADDRESS attribute is present in Binding Responses.  It
     *        indicates the source IP address and port that the server is sending
     *        the response from.  Its syntax is identical to that of MAPPED-
     *        ADDRESS.
     *
     *        Whether it's a server or a client, this indicates the current node's
     *        local address: (ip, port)
     */
    public final SocketAddress sourceAddress;

    public final Hub hub;

    public Node(SocketAddress address, Hub hub) {
        super();
        this.sourceAddress = address;
        this.hub = hub;
    }

    public Node(SocketAddress address) throws SocketException {
        this(address, createHub(address));
    }

    private static Hub createHub(SocketAddress localAddress) throws SocketException {
        Hub hub = new Hub();
        hub.open(localAddress);
        //hub.start();
        return hub;
    }

    protected void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }

    /**
     *  Send data to remote address
     *
     * @param data        - data package to be sent
     * @param destination - remote IP and port
     * @param source      - local IP and port
     * @return count of sent bytes
     */
    public int send(ByteArray data, SocketAddress destination, SocketAddress source) {
        return hub.send(data.getBytes(), destination, source);
    }

    public int send(ByteArray data, SocketAddress destination, int source) {
        SocketAddress address = new InetSocketAddress(source);
        return send(data, destination, address);
    }

    public int send(ByteArray data, SocketAddress destination) {
        return send(data, destination, sourceAddress);
    }

    /**
     *  Received data from any socket
     *
     * @param timeout - in seconds
     * @return data and remote address
     */
    public Cargo receive(float timeout) {
        return hub.receive(timeout);
    }

    public Cargo receive() {
        return receive(2.0f);
    }

    /**
     *  Parse attribute
     *
     * @param attribute -
     * @param context   -
     * @return false on failed
     */
    public abstract boolean parseAttribute(Attribute attribute, Map<String, Object> context);

    /**
     *  Parse package data
     *
     * @param data    - data package received
     * @param context - return with package head and results from body
     * @return false on failed`
     */
    public boolean parseData(ByteArray data, Map<String, Object> context) {
        // 1. parse STUN package
        Package pack = Package.parse(data);
        if (pack == null) {
            info("failed to parse package data: " + data);
            return false;
        }
        // 2. parse attributes
        List<Attribute> attributes = Attribute.parseAll(pack.body);
        for (Attribute item : attributes) {
            // 3. process attribute
            parseAttribute(item, context);
        }
        context.put("head", pack.head);
        return true;
    }
}
