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

import chat.dim.tlv.*;

public class Field extends TagLengthValue {

    public Field(TagLengthValue field) {
        super(field);
    }

    public Field(Data data, FieldName type, FieldValue value) {
        super(data, type, value);
    }

    public Field(FieldName type, FieldValue value) {
        super(type, new FieldLength(value == null ? 0 : value.getLength()), value);
    }


    //
    //  Parser
    //

    private static final Parser parser = new Parser();

    public static List<Field> parseFields(Data data) {
        //noinspection unchecked
        return (List<Field>) parser.parseAll(data);
    }

    protected static class Parser extends TagLengthValue.Parser {

        @Override
        protected FieldName parseTag(Data data) {
            return FieldName.parse(data);
        }

        @Override
        protected FieldLength parseLength(Data data, Tag type) {
            assert type instanceof FieldName : "field name error: " + type;
            return FieldLength.parse(data, (FieldName) type);
        }

        @Override
        protected FieldValue parseValue(Data data, Tag type, Length length) {
            assert type instanceof FieldName : "field name error: " + type;
            assert length instanceof FieldLength : "field length error: " + length;
            return FieldValue.parse(data, (FieldName) type, (FieldLength) length);
        }

        @Override
        protected Field create(Data data, Tag type, Value value) {
            assert type instanceof FieldName : "field name error: " + type;
            assert value == null || value instanceof FieldValue : "field value error: " + value;
            return new Field(data, (FieldName) type, (FieldValue) value);
        }
    }
}
