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

import chat.dim.tlv.Length16;
import chat.dim.tlv.Parser;
import chat.dim.tlv.RawValue;
import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;

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

public class AttributeParser extends Parser<Attribute, AttributeType, Length16, Triad.Value>
        implements TypeParser, LengthParser, ValueParser {

    @Override
    protected TypeParser getTagParser() {
        return this;
    }
    @Override
    protected LengthParser getLengthParser() {
        return this;
    }
    @Override
    protected ValueParser getValueParser() {
        return this;
    }

    @Override
    public AttributeType parseTag(ByteArray data) {
        return AttributeType.from(data);
    }

    @Override
    public Length16 parseLength(ByteArray data, AttributeType type) {
        return Length16.from(data);
    }

    @Override
    public Triad.Value parseValue(ByteArray data, AttributeType type, Length16 length) {
        ValueParser parser = valueParsers.get(type.name);
        if (parser == null) {
            return RawValue.from(data);
        } else {
            return parser.parseValue(data, type, length);
        }
    }

    @Override
    protected Attribute createTriad(ByteArray data, AttributeType type, Length16 length, Triad.Value value) {
        return new Attribute(data, type, length, value);
    }


    //-------- Runtime --------

    private static final Map<String, ValueParser> valueParsers = new HashMap<>();

    public static void register(String type, ValueParser parser) {
        if (parser == null) {
            valueParsers.remove(type);
        } else {
            valueParsers.put(type, parser);
        }
    }
}
