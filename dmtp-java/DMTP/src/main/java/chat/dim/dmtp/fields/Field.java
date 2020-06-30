/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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
package chat.dim.dmtp.fields;

import java.util.List;

import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.tlv.TagLengthValue;
import chat.dim.tlv.Value;

public class Field extends TagLengthValue {

    public Field(byte[] data, FieldName type, FieldValue value) {
        super(data, type, value);
    }

    public Field(FieldName type, FieldValue value) {
        super(type, new FieldLength(value == null ? 0 : value.length), value);
    }

    @Override
    public String toString() {
        return "/* " + getClass() + " */ " + tag + ": " + value;
    }


    //
    //  Parser
    //

    private static final Parser parser = new Parser();

    public static List<Field> parseFields(byte[] data) {
        //noinspection unchecked
        return (List<Field>) parser.parseAll(data);
    }

    protected static class Parser extends TagLengthValue.Parser {

        @Override
        protected Field create(byte[] data, Tag type, Value value) {
            return new Field(data, (FieldName) type, (FieldValue) value);
        }

        @Override
        protected FieldName parseTag(byte[] data) {
            return FieldName.parse(data);
        }

        protected FieldLength parseLength(byte[] data, Tag type) {
            return FieldLength.parse(data, (FieldName) type);
        }

        protected FieldValue parseValue(byte[] data, Tag type, Length length) {
            return FieldValue.parse(data, (FieldName) type, (FieldLength) length);
        }
    }
}
