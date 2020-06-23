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
import java.util.HashMap;
import java.util.Map;

import chat.dim.stun.attributes.Attribute;
import chat.dim.stun.attributes.AttributeType;
import chat.dim.stun.attributes.AttributeValue;
import chat.dim.stun.protocol.Header;
import chat.dim.stun.protocol.Package;
import chat.dim.stun.valus.*;
import chat.dim.tlv.Data;
import chat.dim.tlv.Tag;
import chat.dim.tlv.Value;

/**
 *  Session Traversal Utilities for NAT
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 *  Server nodes
 */

public class Server extends Node {

    public String software = "stun.dim.chat 0.1";

    /*  11.2.3  CHANGED-ADDRESS
     *
     *        The CHANGED-ADDRESS attribute indicates the IP address and port where
     *        responses would have been sent from if the "change IP" and "change
     *        port" flags had been set in the CHANGE-REQUEST attribute of the
     *        Binding Request.  The attribute is always present in a Binding
     *        Response, independent of the value of the flags.  Its syntax is
     *        identical to MAPPED-ADDRESS.
     */
    public SocketAddress changedAddress;

    /*  "Change IP and Port"
     *
     *        When this server A received ChangeRequest with "change IP" and
     *        "change port" flags set, it should redirect this request to the
     *        neighbour server B to (use another address) respond the client.
     *
     *        This address will be the same as CHANGED-ADDRESS by default, but
     *        offer another different IP address here will be better.
     */
    public SocketAddress neighbour;

    /*  "Change Port"
     *
     *        When this server received ChangeRequest with "change port" flag set,
     *        it should respond the client with another port.
     */
    public int changePort;

    public Server(String host, int port, int changePort) throws SocketException {
        super(host, port);
        this.changePort = changePort;
        this.hub.open(host, changePort);
    }

    public Server(int port, int changePort) throws SocketException {
        this("0.0.0.0", port, changePort);
    }

    public Server() throws SocketException {
        this("0.0.0.0", 3478, 3479);
    }

    @Override
    public boolean parseAttribute(Attribute attribute, Map<String, Object> context) {
        Tag type = attribute.tag;
        Value value = attribute.value;
        if (type.equals(AttributeType.MappedAddress)) {
            assert value instanceof MappedAddressValue : "mapped address value error: " + value;
            context.put("MAPPED-ADDRESS", value);
            info("MAPPED-ADDRESS:\t" + value);
        } else if (type.equals(AttributeType.ChangeRequest)) {
            assert value instanceof ChangeRequestValue : "change request value error: " + value;
            context.put("CHANGE-REQUEST", value);
            info("CHANGE-REQUEST: %s" + value);
        } else {
            info("unknown attribute type: " + type);
            return false;
        }
        return true;
    }

    /**
     *  Redirect the request to the neighbor server
     *
     * @param head          -
     * @param clientAddress - client's mapped address
     */
    protected boolean redirect(Header head, SocketAddress clientAddress) {
        InetSocketAddress address = (InetSocketAddress) clientAddress;
        MappedAddressValue value = MappedAddressValue.create(address.getHostString(), address.getPort());
        Attribute attribute = new Attribute(AttributeType.MappedAddress, value);
        // pack
        byte[] body = attribute.data;
        Package pack = Package.create(head.type, head.sn, body);
        assert neighbour != null : "neighbour address not set yet";
        int res = send(pack.data, neighbour);
        return res == pack.length;
    }

    protected boolean respond(Header head, SocketAddress clientAddress, int localPort) {
        InetSocketAddress address = (InetSocketAddress) clientAddress;
        String remoteIP = address.getHostString();
        int remotePort = address.getPort();
        assert sourceAddress != null : "source address not set yet";
        assert changedAddress != null : "changed address not set yet";
        assert localPort > 0 : "local port error";
        String localIP = ((InetSocketAddress) sourceAddress).getHostName();
        address = (InetSocketAddress) changedAddress;
        String changedIP = address.getHostString();
        int changedPort = address.getPort();
        // create attributes
        AttributeValue value;
        // mapped address
        value = MappedAddressValue.create(remoteIP, remotePort);
        byte[] data1 = (new Attribute(AttributeType.MappedAddress, value)).data;
        // xor
        value = XorMappedAddressValue.create(remoteIP, remotePort, head.sn.data);
        byte[] data4 = (new Attribute(AttributeType.XorMappedAddress, value)).data;
        // xor2
        value = XorMappedAddressValue2.create(remoteIP, remotePort, head.sn.data);
        byte[] data5 = (new Attribute(AttributeType.XorMappedAddress2, value)).data;
        // source address
        value = SourceAddressValue.create(localIP, localPort);
        byte[] data2 = (new Attribute(AttributeType.SourceAddress, value)).data;
        // changed address
        value = ChangedAddressValue.create(changedIP, changedPort);
        byte[] data3 = (new Attribute(AttributeType.ChangedAddress, value)).data;
        // software
        value = SoftwareValue.create(software);
        byte[] data6 = (new Attribute(AttributeType.SourceAddress, value)).data;
        // pack
        byte[] body = Data.concat(data1, data2);
        body = Data.concat(body, Data.concat(data3, data4));
        body = Data.concat(body, Data.concat(data5, data6));
        Package pack = Package.create(head.type, head.sn, body);
        int res = send(pack.data, clientAddress, new InetSocketAddress(localIP, localPort));
        return res == pack.length;
    }

    public boolean handle(byte[] data, SocketAddress clientAddress) {
        // parse request data
        Map<String, Object> context = new HashMap<>();
        boolean ok = parseData(data, context);
        Header head = (Header) context.get("head");
        if (!ok || head == null) {
            // received package error
            return false;
        }
        info("received message type: " + head.type);
        ChangeRequestValue value1 = (ChangeRequestValue) context.get("CHANGE-REQUEST");
        if (value1 != null) {
            if (value1.equals(ChangeRequestValue.ChangeIPAndPort)) {
                // redirect for "change IP" and "change port" flags
                return redirect(head, clientAddress);
            } else if (value1.equals(ChangeRequestValue.ChangePort)) {
                // respond with another port for "change port" flag
                return respond(head, clientAddress, changePort);
            }
        }
        MappedAddressValue value2 = (MappedAddressValue) context.get("MAPPED-ADDRESS");
        if (value2 != null) {
            // respond redirected request
            InetSocketAddress address = new InetSocketAddress(value2.ip, value2.port);
            return respond(head, address, changePort);
        } else {
            // respond origin request
            int localPort = ((InetSocketAddress) sourceAddress).getPort();
            return respond(head, clientAddress, localPort);
        }
    }
}
