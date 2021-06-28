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

import chat.dim.tlv.Entry;
import chat.dim.tlv.Length16;
import chat.dim.tlv.RawValue;
import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;

public class Attribute extends Triad<AttributeType, Length16, Entry.Value> {

    public Attribute(Entry<AttributeType, Length16, Entry.Value> tlv) {
        super(tlv);
    }

    public Attribute(ByteArray data, AttributeType type, Length16 length, Entry.Value value) {
        super(data, type, length, value);
    }


    //
    //  Parser
    //
    private static final AttributeParser parser = new AttributeParser();

    public static List<Attribute> parseList(ByteArray data) {
        return parser.parseEntries(data);
    }

    //
    //  Factories
    //

    public static Attribute from(Attribute attribute) {
        return attribute;
    }

    public static Attribute from(Entry<AttributeType, Length16, Entry.Value> tlv) {
        return new Attribute(tlv);
    }

    public static Attribute create(AttributeType type, Entry.Value value) {
        return create(type, null, value);
    }
    public static Attribute create(AttributeType tag, Length16 length, Entry.Value value) {
        if (value == null) {
            value = RawValue.ZERO;
            length = Length16.ZERO;
        } else if (length == null) {
            length = Length16.from(value.getSize());
        }
        ByteArray data = tag.concat(length, value);
        return new Attribute(data, tag, length, value);
    }
}
