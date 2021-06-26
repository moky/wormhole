/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
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
package chat.dim.tlv;

import java.util.List;

import chat.dim.type.ByteArray;

public class Field extends TagLengthValue<StringTag, VarLength, Triad.Value> {

    public Field(Triad<StringTag, VarLength, Value> tlv) {
        super(tlv);
    }

    public Field(ByteArray data, StringTag type, VarLength length, Value value) {
        super(data, type, length, value);
    }

    //
    //  Parser
    //
    private static final FieldParser<Field> parser = new FieldParser<Field>() {
        @Override
        protected Field createTriad(ByteArray data, StringTag type, VarLength length, Value value) {
            return new Field(data, type, length, value);
        }
    };

    public static List<Field> parseFields(ByteArray data) {
        return parser.parseTriads(data);
    }

    public static void register(StringTag type, ValueParser parser) {
        FieldParser.register(type.string, parser);
    }

    //
    //  Factories
    //

    public static Field from(Field field) {
        return field;
    }

    public static Field from(Triad<StringTag, VarLength, Value> tlv) {
        return new Field(tlv);
    }

    public static Field create(StringTag tag) {
        return create(tag, null, null);
    }
    public static Field create(StringTag tag, Value value) {
        return create(tag, null, value);
    }
    public static Field create(StringTag tag, VarLength length, Value value) {
        if (value == null) {
            value = RawValue.ZERO;
            length = VarLength.ZERO;
        } else if (length == null) {
            length = VarLength.from(value.getSize());
        }
        ByteArray data = tag.concat(length, value);
        return new Field(data, tag, length, value);
    }

    /**
     *  TLV Parsers
     *  ~~~~~~~~~~~
     */

    interface TagParser extends Triad.Tag.Parser<StringTag> {
        // just for alias
    }
    interface LengthParser extends Triad.Length.Parser<StringTag, VarLength> {
        // just for alias
    }
    public interface ValueParser extends Triad.Value.Parser<StringTag, VarLength, Triad.Value> {
        // just for alias
    }
}
