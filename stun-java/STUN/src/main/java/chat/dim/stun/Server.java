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
import chat.dim.stun.protocol.MessageType;
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
        super(new InetSocketAddress(host, port));
        this.changePort = changePort;
        this.hub.open(new InetSocketAddress(host, changePort));
    }

    @Override
    public boolean parseAttribute(Attribute attribute, Map<String, Object> context) {
        Tag type = attribute.tag;
        Value value = attribute.value;
        if (type.equals(AttributeType.MappedAddress)) {
            assert value instanceof MappedAddressValue : "mapped address value error: " + value;
            context.put("MAPPED-ADDRESS", value);
        } else if (type.equals(AttributeType.ChangeRequest)) {
            assert value instanceof ChangeRequestValue : "change request value error: " + value;
            context.put("CHANGE-REQUEST", value);
        } else {
            info("unknown attribute type: " + type);
            return false;
        }
        info(type + ":\t" + value);
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
        MappedAddressValue value = new MappedAddressValue(address.getHostString(), address.getPort());
        Attribute attribute = new Attribute(AttributeType.MappedAddress, value);
        // pack
        Package pack = Package.create(head.type, head.sn, attribute);
        assert neighbour != null : "neighbour address not set yet";
        int res = send(pack, neighbour);
        return res == pack.getLength();
    }

    protected boolean respond(Header head, SocketAddress clientAddress, int localPort) {
        // remote (client) address
        InetSocketAddress address = (InetSocketAddress) clientAddress;
        String remoteIP = address.getHostString();
        int remotePort = address.getPort();
        // local (server) address
        assert sourceAddress != null : "source address not set yet";
        String localIP = ((InetSocketAddress) sourceAddress).getHostName();
        assert localPort > 0 : "local port error";
        // changed (another) address
        assert changedAddress != null : "changed address not set yet";
        address = (InetSocketAddress) changedAddress;
        String changedIP = address.getHostString();
        int changedPort = address.getPort();
        // create attributes
        AttributeValue value;
        // mapped address
        value = new MappedAddressValue(remoteIP, remotePort);
        Data data1 = (new Attribute(AttributeType.MappedAddress, value));
        // xor
        value = XorMappedAddressValue.create(remoteIP, remotePort, head.sn.getBytes());
        Data data4 = (new Attribute(AttributeType.XorMappedAddress, value));
        // xor2
        value = XorMappedAddressValue2.create(remoteIP, remotePort, head.sn.getBytes());
        Data data5 = (new Attribute(AttributeType.XorMappedAddress2, value));
        // source address
        value = new SourceAddressValue(localIP, localPort);
        Data data2 = (new Attribute(AttributeType.SourceAddress, value));
        // changed address
        value = new ChangedAddressValue(changedIP, changedPort);
        Data data3 = (new Attribute(AttributeType.ChangedAddress, value));
        // software
        value = SoftwareValue.create(software);
        Data data6 = (new Attribute(AttributeType.Software, value));
        // pack
        Data body = new Data(data1.getLength() + data2.getLength() + data3.getLength()
                + data4.getLength() + data5.getLength() + data6.getLength());

        int offset = 0;
        body.copy(data1, 0, offset, data1.getLength());

        offset += data1.getLength();
        body.copy(data2, 0, offset, data2.getLength());

        offset += data2.getLength();
        body.copy(data3, 0, offset, data3.getLength());

        offset += data3.getLength();
        body.copy(data4, 0, offset, data4.getLength());

        offset += data4.getLength();
        body.copy(data5, 0, offset, data5.getLength());

        offset += data5.getLength();
        body.copy(data6, 0, offset, data6.getLength());
        Package pack = Package.create(MessageType.BindResponse, head.sn, body);
        int res = send(pack, clientAddress, new InetSocketAddress(localIP, localPort));
        return res == pack.getLength();
    }

    public boolean handle(Data data, SocketAddress clientAddress) {
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
            int localPort = ((InetSocketAddress) sourceAddress).getPort();
            return respond(head, clientAddress, localPort);
        } else {
            // respond redirected request
            clientAddress = new InetSocketAddress(mappedAddress.ip, mappedAddress.port);
            return respond(head, clientAddress, changePort);
        }
    }
}
