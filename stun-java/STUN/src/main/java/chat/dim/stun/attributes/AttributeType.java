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
package chat.dim.stun.attributes;

import java.util.HashMap;
import java.util.Map;

import chat.dim.network.DataConvert;
import chat.dim.stun.valus.ChangeRequestValue;
import chat.dim.stun.valus.ChangedAddressValue;
import chat.dim.stun.valus.MappedAddressValue;
import chat.dim.stun.valus.ResponseAddressValue;
import chat.dim.stun.valus.SoftwareValue;
import chat.dim.stun.valus.SourceAddressValue;
import chat.dim.tlv.tags.Tag16;
import chat.dim.type.ByteArray;
import chat.dim.type.UInt16Data;

public class AttributeType extends Tag16 {

    public final String name;

    public AttributeType(UInt16Data data, String name) {
        super(data, data.value, data.endian);
        this.name = name;
    }

    @Override
    public String toString() {
        return name;
    }

    //
    //  Factories
    //

    public static AttributeType from(AttributeType type) {
        return type;
    }

    public static AttributeType from(UInt16Data data) {
        return get(data);
    }

    public static AttributeType from(ByteArray data) {
        if (data.getSize() < 2) {
            return null;
        } else if (data.getSize() > 2) {
            data = data.slice(0, 2);
        }
        return get(DataConvert.getUInt16Data(data));
    }

    // parse tag
    public static AttributeType parse(ByteArray data) {
        return from(data);
    }

    private static synchronized AttributeType get(UInt16Data data) {
        AttributeType type = s_types.get(data.value);
        if (type == null) {
            type = create(data, "Attribute-" + Integer.toHexString(data.value));
        }
        return type;
    }
    private static AttributeType create(UInt16Data data, String name) {
        AttributeType type = new AttributeType(data, name);
        s_types.put(data.value, type);
        return type;
    }
    public static synchronized AttributeType create(int value, String name) {
        UInt16Data data = DataConvert.getUInt16Data(value);
        return create(data, name);
    }

    // Attribute Types in STUN message
    private static final Map<Integer, AttributeType> s_types = new HashMap<>();

    // Comprehension-required range (0x0000-0x7FFF)
    // Comprehension-optional range (0x8000-0xFFFF)

    // [RFC-3489]
    public static final AttributeType MAPPED_ADDRESS     = create(0x0001, "MAPPED-ADDRESS");
    public static final AttributeType RESPONSE_ADDRESS   = create(0x0002, "RESPONSE-ADDRESS");
    public static final AttributeType CHANGE_REQUEST     = create(0x0003, "CHANGE-REQUEST");
    public static final AttributeType SOURCE_ADDRESS     = create(0x0004, "SOURCE-ADDRESS");
    public static final AttributeType CHANGED_ADDRESS    = create(0x0005, "CHANGED-ADDRESS");
    public static final AttributeType USERNAME           = create(0x0006, "USERNAME");
    public static final AttributeType PASSWORD           = create(0x0007, "PASSWORD");
    public static final AttributeType MESSAGE_INTEGRITY  = create(0x0008, "MESSAGE-INTEGRITY");
    public static final AttributeType ERROR_CODE         = create(0x0009, "ERROR-CODE");
    public static final AttributeType UNKNOWN_ATTRIBUTES = create(0x000A, "UNKNOWN-ATTRIBUTES");
    public static final AttributeType REFLECTED_FROM     = create(0x000B, "REFLECTED-FROM");

    // [RFC-5389]
    public static final AttributeType REALM              = create(0x0014, "REALM");
    public static final AttributeType NONCE              = create(0x0015, "NONCE");
    public static final AttributeType XOR_MAPPED_ADDRESS = create(0x0020, "XOR-MAPPED-ADDRESS(0020)");

    public static final AttributeType XOR_MAPPED_ADDRESS_8020 = create(0x8020, "XOR-MAPPED-ADDRESS(8020)");
    public static final AttributeType XOR_ONLY           = create(0x8021, "XOR-ONLY");
    public static final AttributeType SOFTWARE           = create(0x8022, "SOFTWARE");
    public static final AttributeType ALTERNATE_SERVER   = create(0x8023, "ALTERNATE-SERVER");
    public static final AttributeType FINGERPRINT        = create(0x8028, "FINGERPRINT");

    public static void register(AttributeType type, ValueParser parser) {
        AttributeParser.register(type.name, parser);
    }

    static {
        //
        //  Register attribute parsers
        //
        register(MAPPED_ADDRESS,     MappedAddressValue::parse);
        //register(XOR_MAPPED_ADDRESS,  XorMappedAddressValue::parse);
        //register(XOR_MAPPED_ADDRESS_8020, XorMappedAddressValue2::parse);

        register(RESPONSE_ADDRESS,   ResponseAddressValue::parse);
        register(CHANGE_REQUEST,     ChangeRequestValue::parse);
        register(SOURCE_ADDRESS,     SourceAddressValue::parse);
        register(CHANGED_ADDRESS,    ChangedAddressValue::parse);

        register(SOFTWARE,           SoftwareValue::parse);
    }
}
