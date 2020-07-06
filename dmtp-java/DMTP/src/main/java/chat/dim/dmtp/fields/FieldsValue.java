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

import java.util.*;

import chat.dim.dmtp.values.BinaryValue;
import chat.dim.dmtp.values.ByteValue;
import chat.dim.dmtp.values.StringValue;
import chat.dim.dmtp.values.TimestampValue;
import chat.dim.tlv.Data;
import chat.dim.tlv.MutableData;

public class FieldsValue extends FieldValue implements Map<String, Object> {

    protected final Map<String, Object> dictionary;

    public FieldsValue(Data data, List<Field> fields) {
        super(data);
        dictionary = new HashMap<>();
        for (Field item : fields) {
            setField((FieldName) item.tag, (FieldValue) item.value);
        }
    }

    public FieldsValue(List<Field> fields) {
        this(build(fields), fields);
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

    protected void setField(FieldName tag, FieldValue value) {
        String key = tag.name;
        if (value == null) {
            dictionary.remove(key);
        } else if (value instanceof StringValue) {
            dictionary.put(key, ((StringValue) value).string);
        } else if (value instanceof ByteValue) {
            dictionary.put(key, ((ByteValue) value).value);
        } else if (value instanceof TimestampValue) {
            dictionary.put(key, ((TimestampValue) value).value);
        } else if (value instanceof BinaryValue) {
            dictionary.put(key, value);
        } else {
            System.out.printf("%s> unknown field: %s -> %s\n", getClass(), tag, value);
        }
    }

    public static FieldsValue parse(Data data, FieldName type, FieldLength length) {
        // parse fields
        List<Field> fields = Field.parseFields(data);
        return new FieldsValue(data, fields);
    }

    //
    //  Map interfaces
    //

    @Override
    public String toString() {
        return dictionary.toString();
    }

    @Override
    public int size() {
        return dictionary.size();
    }

    @Override
    public boolean isEmpty() {
        return dictionary.isEmpty();
    }

    @Override
    public boolean containsKey(Object key) {
        if (key instanceof FieldName) {
            key = ((FieldName) key).name;
        }
        return dictionary.containsKey(key);
    }

    @Override
    public boolean containsValue(Object value) {
        return dictionary.containsValue(value);
    }

    @Override
    public Object get(Object key) {
        if (key instanceof FieldName) {
            key = ((FieldName) key).name;
        }
        return dictionary.get(key);
    }

    @Override
    public Object put(String key, Object value) {
        throw new UnsupportedOperationException("immutable!");
        //return dictionary.put(key, value);
    }

    @Override
    public Object remove(Object key) {
        throw new UnsupportedOperationException("immutable!");
        //return dictionary.remove(key);
    }

    @Override
    public void putAll(Map<? extends String, ?> m) {
        throw new UnsupportedOperationException("immutable!");
    }

    @Override
    public void clear() {
        throw new UnsupportedOperationException("immutable!");
    }

    @Override
    public Set<String> keySet() {
        return dictionary.keySet();
    }

    @Override
    public Collection<Object> values() {
        return dictionary.values();
    }

    @Override
    public Set<Entry<String, Object>> entrySet() {
        return dictionary.entrySet();
    }
}
