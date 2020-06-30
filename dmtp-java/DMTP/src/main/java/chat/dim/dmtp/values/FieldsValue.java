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
package chat.dim.dmtp.values;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import chat.dim.dmtp.fields.Field;
import chat.dim.dmtp.fields.FieldLength;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.dmtp.fields.FieldValue;

public class FieldsValue extends FieldValue {

    public final List<Field> fields;

    public FieldsValue(byte[] data, List<Field> fields) {
        super(data);
        // set fields
        this.fields = fields;
        for (Field item : fields) {
            setField(item);
        }
    }

    public FieldsValue(List<Field> fields) {
        this(build(fields), fields);
    }

    private static byte[] build(List<Field> fields) {
        int length = 0;
        for (Field item : fields) {
            length += item.length;
        }
        byte[] data = new byte[length];
        int pos = 0;
        for (Field item : fields) {
            System.arraycopy(item.data, 0, data, pos, item.length);
            pos += item.length;
        }
        return data;
    }

    protected void setField(Field field) {
        // TODO: implement by subclass
        System.out.printf("%s> unknown field: %s -> %s", getClass(), field.tag, field.value);
    }

    public static FieldsValue parse(byte[] data, FieldName type, FieldLength length) {
        // check length
        if (length == null || length.value == 0) {
            //throw new ArrayIndexOutOfBoundsException("length error: " + length);
            return null;
        } else {
            int len = length.getIntValue();
            int dataLen = data.length;
            if (len < 0 || len > dataLen) {
                //throw new ArrayIndexOutOfBoundsException("data length error: " + data.length + ", " + length.value);
                return null;
            } else if (len < dataLen) {
                data = slice(data, 0, len);
            }
        }
        // parse fields
        List<Field> fields = Field.parseFields(data);
        return new FieldsValue(data, fields);
    }

    public Map<String, Object> toDictionary() {
        Map<String, Object> dictionary = new HashMap<>();
        String name;
        Object value;
        Object same;
        List<Object> array;
        for (Field item : fields) {
            name = item.tag.toString();
            value = item.value;
            if (value instanceof FieldsValue) {
                value = ((FieldsValue) value).toDictionary();
            }
            same = dictionary.get(name);
            if (same == null) {
                dictionary.put(name, value);
            } else if (same instanceof List) {
                //noinspection unchecked
                array = (List<Object>) same;
                // add value to the array with the same name
                array.add(value);
            } else {
                // convert values with the same name to an array
                array = new ArrayList<>();
                array.add(same);
                array.add(value);
                dictionary.put(name, array);
            }
        }
        return dictionary;
    }
}
