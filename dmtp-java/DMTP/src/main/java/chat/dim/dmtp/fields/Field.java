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

import chat.dim.tlv.TagLengthValue;
import chat.dim.type.ByteArray;

import java.util.List;

public class Field extends TagLengthValue<FieldName, FieldLength, FieldValue> {

    public Field(TagLengthValue<FieldName, FieldLength, FieldValue> field) {
        super(field);
    }

    public Field(ByteArray data, FieldName type, FieldLength length, FieldValue value) {
        super(data, type, length, value);
    }

    public Field(FieldName type, FieldLength length, FieldValue value) {
        super(type, getLength(length, value), value);
    }

    public Field(FieldName type, FieldValue value) {
        super(type, getLength(null, value), value);
    }

    protected static FieldLength getLength(FieldLength length, FieldValue value) {
        if (length != null) {
            return length;
        } else if (value != null) {
            return new FieldLength(value.getLength());
        } else {
            return new FieldLength(0);
        }
    }

    //
    //  Parser
    //
    private static final FieldParser parser = new FieldParser();

    public static List<Field> parseAll(ByteArray data) {
        return parser.parseAll(data);
    }
}
