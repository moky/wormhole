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

import chat.dim.tlv.Tag;
import chat.dim.tlv.UInt16Data;

public class AttributeType extends Tag {

    public final int value;
    private final String name;

    public AttributeType(int value, byte[] data, String name) {
        super(data);
        this.value = value;
        this.name = name;
        s_types.put(value, this);
    }

    public AttributeType(int value, byte[] data) {
        this(value, data, "Attribute-" + Integer.toHexString(value));
    }

    public AttributeType(int value, String name) {
        this(value, UInt16Data.intToBytes(value, 2), name);
    }

    public AttributeType(int value) {
        this(value, UInt16Data.intToBytes(value, 2));
    }

    @Override
    public boolean equals(Object other) {
        if (other instanceof AttributeType) {
            return equals(((AttributeType) other).value);
        }
        return this == other;
    }
    public boolean equals(int other) {
        return value == other;
    }

    @Override
    public int hashCode() {
        return Integer.hashCode(value);
    }

    @Override
    public String toString() {
        return name;
    }

    //
    //  Factory
    //

    public static AttributeType parse(byte[] data) {
        int length = data.length;
        if (length < 2) {
            return null;
        } else if (length > 2) {
            data = slice(data, 0, 2);
        }
        int value = (int) UInt16Data.bytesToInt(data);
        return getInstance(value);
    }

    public static synchronized AttributeType getInstance(int value) {
        AttributeType type = s_types.get(value);
        if (type == null) {
            type = new AttributeType(value);
        }
        return type;
    }

    // Attribute Types in STUN message
    private static final Map<Integer, AttributeType> s_types = new HashMap<>();

    // Comprehension-required range (0x0000-0x7FFF)
    // Comprehension-optional range (0x8000-0xFFFF)

    // [RFC-3489]
    public static AttributeType MappedAddress     = new AttributeType(0x0001, "MAPPED-ADDRESS");
    public static AttributeType ResponseAddress   = new AttributeType(0x0002, "RESPONSE-ADDRESS");
    public static AttributeType ChangeRequest     = new AttributeType(0x0003, "CHANGE-REQUEST");
    public static AttributeType SourceAddress     = new AttributeType(0x0004, "SOURCE-ADDRESS");
    public static AttributeType ChangedAddress    = new AttributeType(0x0005, "CHANGED-ADDRESS");
    public static AttributeType Username          = new AttributeType(0x0006, "USERNAME");
    public static AttributeType Password          = new AttributeType(0x0007, "PASSWORD");
    public static AttributeType MessageIntegrity  = new AttributeType(0x0008, "MESSAGE-INTEGRITY");
    public static AttributeType ErrorCode         = new AttributeType(0x0009, "ERROR-CODE");
    public static AttributeType UnknownAttributes = new AttributeType(0x000A, "UNKNOWN-ATTRIBUTES");
    public static AttributeType ReflectedFrom     = new AttributeType(0x000B, "REFLECTED-FROM");

    // [RFC-5389]
    public static AttributeType Realm             = new AttributeType(0x0014, "REALM");
    public static AttributeType Nonce             = new AttributeType(0x0015, "NONCE");
    public static AttributeType XorMappedAddress  = new AttributeType(0x0020, "XOR-MAPPED-ADDRESS(0020)");

    public static AttributeType XorMappedAddress2 = new AttributeType(0x8020, "XOR-MAPPED-ADDRESS(8020)");
    public static AttributeType XorOnly           = new AttributeType(0x8021, "XOR-ONLY");
    public static AttributeType Software          = new AttributeType(0x8022, "SOFTWARE");
    public static AttributeType AlternateServer   = new AttributeType(0x8023, "ALTERNATE-SERVER");
    public static AttributeType Fingerprint       = new AttributeType(0x8028, "FINGERPRINT");
}
