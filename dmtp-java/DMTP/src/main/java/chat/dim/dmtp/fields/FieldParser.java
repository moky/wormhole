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

import chat.dim.tlv.Parser;
import chat.dim.type.ByteArray;
import chat.dim.type.VarIntData;

public class FieldParser extends Parser<Field, FieldName, FieldLength, FieldValue> {

    @Override
    public FieldName parseTagField(ByteArray data) {
        int pos = data.find('\0');
        if (pos < 0) {
            throw new IndexOutOfBoundsException("Field name error: " + data);
        }
        ++pos;  // includes the tail '\0'
        if (pos < data.getLength()) {
            data = data.slice(0, pos);
        }
        return new FieldName(data);
    }

    @Override
    public FieldLength parseLengthField(ByteArray data, FieldName type) {
        if (data.getLength() < 1) {
            throw new IndexOutOfBoundsException("Field length error: " + data);
        }
        return new FieldLength(VarIntData.from(data));
    }

    @Override
    public FieldValue parseValueField(ByteArray data, FieldName type, FieldLength length) {
        int valueLength = length.getIntValue();
        if (data.getLength() < valueLength) {
            throw new IndexOutOfBoundsException("Field value error: " + data.getLength());
        } else if (data.getLength() > valueLength) {
            data = data.slice(0, valueLength);
        }
        return FieldValue.parse(data, type, length);
    }

    @Override
    protected Field createTriad(ByteArray data, FieldName type, FieldLength length, FieldValue value) {
        return new Field(data, type, length, value);
    }
}
