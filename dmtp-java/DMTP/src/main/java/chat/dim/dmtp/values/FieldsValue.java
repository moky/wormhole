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
import chat.dim.tlv.Data;
import chat.dim.tlv.MutableData;

public class FieldsValue extends FieldValue {

    private List<Field> fields = null;

    public FieldsValue(Data data) {
        super(data);
    }

    public FieldsValue(List<Field> fields) {
        this(build(fields));
    }

    private static Data build(List<Field> fields) {
        int length = 0;
        for (Field item : fields) {
            length += item.getLength();
        }
        MutableData data = new MutableData(length);
        for (Field item : fields) {
            data.append(item);
        }
        return data;
    }

    @Override
    public String toString() {
        return toDictionary().toString();
    }

    protected void setField(Field field) {
        // TODO: implement by subclass
        System.out.printf("%s> unknown field: %s -> %s\n", getClass(), field.tag, field.value);
    }

    public void setFields(List<Field> fields) {
        for (Field item : fields) {
            setField(item);
        }
        this.fields = fields;
    }

    public static FieldsValue parse(Data data, FieldName type, FieldLength length) {
        // parse fields
        List<Field> fields = Field.parseFields(data);
        FieldsValue value = new FieldsValue(data);
        value.setFields(fields);
        return value;
    }

    public Map<String, Object> toDictionary() {
        Map<String, Object> dictionary = new HashMap<>();
        if (fields == null) {
            return dictionary;
        }
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
