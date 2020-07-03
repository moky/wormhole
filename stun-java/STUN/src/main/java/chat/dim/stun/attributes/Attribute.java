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

import java.util.List;

import chat.dim.tlv.*;

/*
 *    STUN Attributes
 *    ~~~~~~~~~~~~~~~
 *
 *   After the STUN header are zero or more attributes.  Each attribute
 *   MUST be TLV encoded, with a 16-bit type, 16-bit length, and value.
 *   Each STUN attribute MUST end on a 32-bit boundary.  As mentioned
 *   above, all fields in an attribute are transmitted most significant
 *   bit first.
 *
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |         Type                  |            Length             |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Value (variable)                ....
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 *                    Figure 4: Format of STUN Attributes
 */

public class Attribute extends TagLengthValue {

    public Attribute(TagLengthValue attribute) {
        super(attribute);
    }

    public Attribute(Data data, AttributeType type, AttributeValue value) {
        super(data, type, value);
    }

    public Attribute(AttributeType type, AttributeValue value) {
        super(type, new AttributeLength(value == null ? 0 : value.getLength()), value);
    }

    //
    //  Parser
    //

    private static final Parser parser = new Parser();

    public static List<Attribute> parseAttributes(Data data) {
        //noinspection unchecked
        return (List<Attribute>) parser.parseAll(data);
    }

    protected static class Parser extends TagLengthValue.Parser {

        @Override
        protected AttributeType parseTag(Data data) {
            return AttributeType.parse(data);
        }

        @Override
        protected AttributeLength parseLength(Data data, Tag type) {
            assert type instanceof AttributeType : "attribute type error: " + type;
            return AttributeLength.parse(data, (AttributeType) type);
        }

        @Override
        protected AttributeValue parseValue(Data data, Tag type, Length length) {
            assert type instanceof AttributeType : "attribute type error: " + type;
            assert length instanceof AttributeLength : "attribute length error: " + length;
            return AttributeValue.parse(data, (AttributeType) type, (AttributeLength) length);
        }

        @Override
        protected Attribute create(Data data, Tag type, Value value) {
            assert type instanceof AttributeType : "attribute type error: " + type;
            assert value == null || value instanceof AttributeValue : "attribute value error: " + value;
            return new Attribute(data, (AttributeType) type, (AttributeValue) value);
        }
    }
}
