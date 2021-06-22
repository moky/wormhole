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
import chat.dim.stun.protocol.Header;
import chat.dim.stun.protocol.MessageType;
import chat.dim.stun.protocol.Package;
import chat.dim.stun.protocol.TransactionID;
import chat.dim.stun.valus.ChangeRequestValue;
import chat.dim.stun.valus.ChangedAddressValue;
import chat.dim.stun.valus.MappedAddressValue;
import chat.dim.stun.valus.SoftwareValue;
import chat.dim.stun.valus.SourceAddressValue;
import chat.dim.stun.valus.XorMappedAddressValue;
import chat.dim.stun.valus.XorMappedAddressValue2;
import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;
import chat.dim.udp.Cargo;

/**
 *  Session Traversal Utilities for NAT
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 *  Client nodes
 */

public class Client extends Node {

    public int retries = 3;

    public Client(String host, int port) throws SocketException {
        super(new InetSocketAddress(host, port));
    }

    @Override
    public boolean parseAttribute(Attribute attribute, Map<String, Object> context) {
        AttributeType type = attribute.tag;
        Triad.Value value = attribute.value;
        if (type.equals(AttributeType.MAPPED_ADDRESS)) {
            assert value instanceof MappedAddressValue : "mapped address value error: " + value;
            context.put("MAPPED-ADDRESS", value);
        } else if (type.equals(AttributeType.XOR_MAPPED_ADDRESS)) {
            if (!(value instanceof XorMappedAddressValue)) {
                // XOR and parse again
                ByteArray factor = (ByteArray) context.get("trans_id");
                ByteArray data = XorMappedAddressValue.xor(value, factor);
                value = XorMappedAddressValue.from(data);
            }
            if (value != null) {
                context.put("MAPPED-ADDRESS", value);
            }
        } else if (type.equals(AttributeType.XOR_MAPPED_ADDRESS_8020)) {
            if (!(value instanceof XorMappedAddressValue2)) {
                // XOR and parse again
                ByteArray factor = (ByteArray) context.get("trans_id");
                ByteArray data = XorMappedAddressValue2.xor(value, factor);
                value = XorMappedAddressValue2.from(data);
            }
            if (value != null) {
                context.put("MAPPED-ADDRESS", value);
            }
        } else if (type.equals(AttributeType.CHANGED_ADDRESS)) {
            assert value instanceof ChangedAddressValue : "change address value error: " + value;
            context.put("CHANGED-ADDRESS", value);
        } else if (type.equals(AttributeType.SOURCE_ADDRESS)) {
            assert value instanceof SourceAddressValue : "source address value error: " + value;
            context.put("SOURCE-ADDRESS", value);
        } else if (type.equals(AttributeType.SOFTWARE)) {
            assert value instanceof SoftwareValue : "software value error: " + value;
            context.put("SOFTWARE", value);
        } else {
            info("unknown attribute type: " + type);
            return false;
        }
        info(type + ":\t" + value);
        return true;
    }

    private Map<String, Object> bindRequest(ByteArray body, SocketAddress serverAddress) {
        // 1. create STUN message package
        Package req = Package.create(MessageType.BindRequest, null, body);
        TransactionID sn = req.head.sn;
        // 2. send and get response
        int count = 0;
        int size;
        Cargo cargo;
        while (true) {
            size = send(req, serverAddress);
            if (size != req.getSize()) {
                // failed to send data
                return null;
            }
            cargo = receive();
            if (cargo == null) {
                if (count < retries) {
                    count += 1;
                    info("(" + count + "/" + retries + ") receive nothing");
                } else {
                    // failed to receive data
                    return null;
                }
            } else {
                info("received " + cargo.data.length + " bytes from " + cargo.source);
                break;
            }
        }
        // 3. parse response
        Map<String, Object> context = new HashMap<>();
        context.put("trans_id", sn);
        if (!parseData(new Data(cargo.data), context)) {
            return null;
        }
        Header head = (Header) context.get("head");
        if (head == null || !head.type.equals(MessageType.BindResponse) || !head.sn.equals(sn)) {
            // received package error
            return null;
        }
        return context;
    }

    /** [RFC] https://www.ietf.org/rfc/rfc3489.txt
     *
     *     Rosenberg, et al.           Standards Track                    [Page 19]
     *
     *     RFC 3489                          STUN                        March 2003
     *
     *
     *     The flow makes use of three tests.  In test I, the client sends a
     *     STUN Binding Request to a server, without any flags set in the
     *     CHANGE-REQUEST attribute, and without the RESPONSE-ADDRESS attribute.
     *     This causes the server to send the response back to the address and
     *     port that the request came from.  In test II, the client sends a
     *     Binding Request with both the "change IP" and "change port" flags
     *     from the CHANGE-REQUEST attribute set.  In test III, the client sends
     *     a Binding Request with only the "change port" flag set.
     */

    private Map<String, Object> test_1(SocketAddress serverAddress) {
        info("[Test 1] sending empty request ... " + serverAddress);
        return bindRequest(Data.ZERO, serverAddress);
    }

    private Map<String, Object> test_2(SocketAddress serverAddress) {
        info("[Test 2] sending ChangeIPAndPort request ... " + serverAddress);
        Attribute item = Attribute.create(AttributeType.CHANGE_REQUEST, ChangeRequestValue.ChangeIPAndPort);
        return bindRequest(item, serverAddress);
    }

    private Map<String, Object> test_3(SocketAddress serverAddress) {
        info("[Test 1] sending ChangePort request ... " + serverAddress);
        Attribute item = Attribute.create(AttributeType.CHANGE_REQUEST, ChangeRequestValue.ChangePort);
        return bindRequest(item, serverAddress);
    }

    public Map<String, Object> getNatType(SocketAddress serverAddress) {
        // 1. Test I
        Map<String, Object> res1 = test_1(serverAddress);
        if (res1 == null) {
            /*  The client begins by initiating test I.  If this test yields no
             *  response, the client knows right away that it is not capable of UDP
             *  connectivity.
             */
            res1 = new HashMap<>();
            res1.put("NAT", NatType.UDPBlocked);
            return res1;
        }
        /*  If the test produces a response, the client examines the MAPPED-ADDRESS
         *  attribute.  If this address and port are the same as the local IP
         *  address and port of the socket used to send the request, the client
         *  knows that it is not NATed.  It executes test II.
         */
        MappedAddressValue ma1 = (MappedAddressValue) res1.get("MAPPED-ADDRESS");
        InetSocketAddress address = (InetSocketAddress) sourceAddress;
        // 2. Test II
        Map<String, Object> res2 = test_2(serverAddress);
        if (ma1 != null && ma1.port == address.getPort() && ma1.ip.equals(address.getHostString())) {
            /*  If a response is received, the client knows that it has open access
             *  to the Internet (or, at least, its behind a firewall that behaves
             *  like a full-cone NAT, but without the translation).  If no response
             *  is received, the client knows its behind a symmetric UDP firewall.
             */
            if (res2 == null) {
                res1.put("NAT", NatType.SymmetricFirewall);
                return res1;
            } else {
                res2.put("NAT", NatType.OpenInternet);
                return res2;
            }
        } else if (res2 != null) {
            /*  In the event that the IP address and port of the socket did not match
             *  the MAPPED-ADDRESS attribute in the response to test I, the client
             *  knows that it is behind a NAT.  It performs test II.  If a response
             *  is received, the client knows that it is behind a full-cone NAT.
             */
            res2.put("NAT", NatType.FullConeNAT);
            return res2;
        }
        /*  If no response is received, it performs test I again, but this time,
         *  does so to the address and port from the CHANGED-ADDRESS attribute
         *  from the response to test I.
         */
        ChangedAddressValue ca1 = (ChangedAddressValue) res1.get("CHANGED-ADDRESS");
        if (ca1 == null) {
            res1.put("NAT", "Changed-Address not found");
            return res1;
        }
        // 3. Test I'
        address = new InetSocketAddress(ca1.ip, ca1.port);
        Map<String, Object> res11 = test_1(address);
        if (res11 == null) {
            //throw new NullPointerException("network error");
            res1.put("NAT", "Change address failed");
            return res1;
        }
        MappedAddressValue ma11 = (MappedAddressValue) res11.get("MAPPED-ADDRESS");
        if (ma11 == null || ma1 == null || ma11.port != ma1.port || !ma11.ip.equals(ma1.ip)) {
            /*  If the IP address and port returned in the MAPPED-ADDRESS attribute
             *  are not the same as the ones from the first test I, the client
             *  knows its behind a symmetric NAT.
             */
            res11.put("NAT", NatType.SymmetricNAT);
            return res11;
        }
        /*  If the address and port are the same, the client is either behind a
         *  restricted or port restricted NAT.  To make a determination about
         *  which one it is behind, the client initiates test III.  If a response
         *  is received, its behind a restricted NAT, and if no response is
         *  received, its behind a port restricted NAT.
         */
        // 4. Test III
        Map<String, Object> res3 = test_3(serverAddress);
        if (res3 == null) {
            res11.put("NAT", NatType.PortRestrictedNAT);
            return res11;
        } else {
            res3.put("NAT", NatType.RestrictedNAT);
            return res3;
        }
    }
}
