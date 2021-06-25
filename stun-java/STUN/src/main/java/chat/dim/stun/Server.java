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
import java.util.HashMap;
import java.util.Map;

import chat.dim.stun.attributes.Attribute;
import chat.dim.stun.attributes.AttributeType;
import chat.dim.stun.protocol.Header;
import chat.dim.stun.protocol.MessageType;
import chat.dim.stun.protocol.Package;
import chat.dim.stun.valus.ChangeRequestValue;
import chat.dim.stun.valus.ChangedAddressValue;
import chat.dim.stun.valus.MappedAddressValue;
import chat.dim.stun.valus.SoftwareValue;
import chat.dim.stun.valus.SourceAddressValue;
import chat.dim.stun.valus.XorMappedAddressValue;
import chat.dim.stun.valus.XorMappedAddressValue2;
import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;
import chat.dim.type.MutableData;

/**
 *  Session Traversal Utilities for NAT
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 *  Server nodes
 */

public abstract class Server extends Node {

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
    public InetSocketAddress changedAddress;

    /*  "Change IP and Port"
     *
     *        When this server A received CHANGE-REQUEST with "change IP" and
     *        "change port" flags set, it should redirect this request to the
     *        neighbour server B to (use another address) respond the client.
     *
     *        This address will be the same as CHANGED-ADDRESS by default, but
     *        offer another different IP address here will be better.
     */
    public InetSocketAddress neighbour;

    /*  "Change Port"
     *
     *        When this server received CHANGE-REQUEST with "change port" flag set,
     *        it should respond the client with another port.
     */
    public int changePort;

    public Server(String host, int port, int changePort) {
        super(new InetSocketAddress(host, port));
        this.changePort = changePort;
    }

    /**
     *  Redirect the request to the neighbor server
     *
     * @param head          -
     * @param clientAddress - client's mapped address
     */
    private boolean redirect(Header head, InetSocketAddress clientAddress) {
        MappedAddressValue value = MappedAddressValue.create(clientAddress.getHostString(), clientAddress.getPort());
        Attribute attribute = Attribute.create(AttributeType.MAPPED_ADDRESS, value);
        // pack
        Package pack = Package.create(head.type, head.sn, attribute);
        assert neighbour != null : "neighbour address not set yet";
        int res = send(pack.getBytes(), neighbour, sourceAddress);
        return res == pack.getSize();
    }

    private boolean respond(Header head, InetSocketAddress clientAddress, int localPort) {
        // remote (client) address
        String remoteIP = clientAddress.getHostString();
        int remotePort = clientAddress.getPort();
        // local (server) address
        assert sourceAddress != null : "source address not set yet";
        String localIP = sourceAddress.getHostName();
        assert localPort > 0 : "local port error";
        // changed (another) address
        assert changedAddress != null : "changed address not set yet";
        String changedIP = changedAddress.getHostString();
        int changedPort = changedAddress.getPort();
        // create attributes
        Triad.Value value;
        // mapped address
        value = MappedAddressValue.create(remoteIP, remotePort);
        ByteArray data1 = Attribute.create(AttributeType.MAPPED_ADDRESS, value);
        // xor
        value = XorMappedAddressValue.create(remoteIP, remotePort, head.sn);
        ByteArray data4 = Attribute.create(AttributeType.XOR_MAPPED_ADDRESS, value);
        // xor2
        value = XorMappedAddressValue2.create(remoteIP, remotePort, head.sn);
        ByteArray data5 = Attribute.create(AttributeType.XOR_MAPPED_ADDRESS_8020, value);
        // source address
        value = SourceAddressValue.create(localIP, localPort);
        ByteArray data2 = Attribute.create(AttributeType.SOURCE_ADDRESS, value);
        // changed address
        value = ChangedAddressValue.create(changedIP, changedPort);
        ByteArray data3 = Attribute.create(AttributeType.CHANGED_ADDRESS, value);
        // software
        value = SoftwareValue.from(software);
        ByteArray data6 = Attribute.create(AttributeType.SOFTWARE, value);
        // pack
        MutableData body = new MutableData(data1.getSize() + data2.getSize() + data3.getSize()
                + data4.getSize() + data5.getSize() + data6.getSize());
        body.append(data1);
        body.append(data2);
        body.append(data3);
        body.append(data4);
        body.append(data5);
        body.append(data6);
        Package pack = Package.create(MessageType.BindResponse, head.sn, body);
        int res = send(pack.getBytes(), clientAddress, new InetSocketAddress(localIP, localPort));
        return res == pack.getSize();
    }

    public boolean handle(ByteArray data, InetSocketAddress clientAddress) {
        // parse request data
        Map<String, Object> context = new HashMap<>();
        boolean ok = parseData(data, context);
        Header head = (Header) context.get("head");
        if (!ok || head == null || !head.type.equals(MessageType.BindRequest)) {
            // received package error
            return false;
        }
        info("received message type: " + head.type);
        ChangeRequestValue changeRequest = (ChangeRequestValue) context.get("CHANGE-REQUEST");
        if (changeRequest != null) {
            if (changeRequest.equals(ChangeRequestValue.ChangeIPAndPort)) {
                // redirect for "change IP" and "change port" flags
                return redirect(head, clientAddress);
            } else if (changeRequest.equals(ChangeRequestValue.ChangePort)) {
                // respond with another port for "change port" flag
                return respond(head, clientAddress, changePort);
            }
        }
        MappedAddressValue mappedAddress = (MappedAddressValue) context.get("MAPPED-ADDRESS");
        if (mappedAddress == null) {
            // respond origin request
            int localPort = sourceAddress.getPort();
            return respond(head, clientAddress, localPort);
        } else {
            // respond redirected request
            clientAddress = new InetSocketAddress(mappedAddress.ip, mappedAddress.port);
            return respond(head, clientAddress, changePort);
        }
    }
}
