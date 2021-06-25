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
import java.util.List;
import java.util.Map;

import chat.dim.stun.attributes.Attribute;
import chat.dim.stun.attributes.AttributeType;
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
    public final InetSocketAddress sourceAddress;

    public Node(InetSocketAddress address) {
        super();
        sourceAddress = address;
    }

    protected void info(String msg) {
        // logs
    }

    /**
     *  Send data to remote address
     *
     * @param data        - data package to be sent
     * @param destination - remote IP and port
     * @param source      - local IP and port
     * @return count of sent bytes
     */
    public abstract int send(byte[] data, SocketAddress destination, SocketAddress source);

    /**
     *  Parse attribute
     *
     * @param attribute - origin attribute
     * @param context   - context
     * @return null on failed
     */
    protected Attribute parseAttribute(Attribute attribute, Map<String, Object> context) {
        AttributeType type = attribute.tag;
        Triad.Value value = attribute.value;
        if (type.equals(AttributeType.CHANGE_REQUEST)) {
            assert value instanceof ChangeRequestValue : "change request value error: " + value;
            context.put("CHANGE-REQUEST", value);
        } else if (type.equals(AttributeType.MAPPED_ADDRESS)) {
            assert value instanceof MappedAddressValue : "mapped address value error: " + value;
            context.put("MAPPED-ADDRESS", value);
        } else if (type.equals(AttributeType.XOR_MAPPED_ADDRESS)) {
            if (!(value instanceof XorMappedAddressValue)) {
                // XOR and parse again
                ByteArray factor = (ByteArray) context.get("trans_id");
                value = XorMappedAddressValue.create(value, factor);
            }
            if (value != null) {
                context.put("MAPPED-ADDRESS", value);
            }
        } else if (type.equals(AttributeType.XOR_MAPPED_ADDRESS_8020)) {
            if (!(value instanceof XorMappedAddressValue2)) {
                // XOR and parse again
                ByteArray factor = (ByteArray) context.get("trans_id");
                value = XorMappedAddressValue2.create(value, factor);
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
            return null;
        }
        info(type + ":\t" + value);
        return new Attribute(attribute, type, attribute.length, value);
    }

    /**
     *  Parse package data
     *
     * @param data    - data package received
     * @param context - return with package head and results from body
     * @return false on failed`
     */
    protected boolean parseData(ByteArray data, Map<String, Object> context) {
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
