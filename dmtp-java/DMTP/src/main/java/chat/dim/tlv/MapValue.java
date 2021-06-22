/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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

import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import chat.dim.type.ByteArray;

public class MapValue<F extends Field> extends RawValue implements Map<Triad.Tag, Triad.Value> {

    private final Map<Triad.Tag, Triad.Value> dictionary = new HashMap<>();

    public MapValue(ByteArray data, List<F> fields) {
        super(data);
        for (F item : fields) {
            if (item.getValue() == null) {
                dictionary.remove(item.getTag());
            } else {
                dictionary.put(item.getTag(), item.getValue());
            }
        }
    }

    public MapValue(List<F> fields) {
        this(concat(fields), fields);
    }

    private static<F extends Field> ByteArray concat(List<F> fields) {
        if (fields == null || fields.isEmpty()) {
            return null;
        }
        ByteArray data = fields.get(0);
        for (int i = 1; i < fields.size(); ++i) {
            data = data.concat(fields.get(i));
        }
        return data;
    }

    public String getStringValue(StringTag tag) {
        Triad.Value value = dictionary.get(tag);
        if (value instanceof StringValue) {
            return ((StringValue) value).string;
        } else {
            return null;
        }
    }

    public long getLongValue(StringTag tag) {
        Triad.Value value = dictionary.get(tag);
        if (value instanceof Value32) {
            return ((Value32) value).value;
        } else {
            return 0;
        }
    }

    public int getShortValue(StringTag tag) {
        Triad.Value value = dictionary.get(tag);
        if (value instanceof Value16) {
            return ((Value16) value).value;
        } else {
            return 0;
        }
    }

    public int getByteValue(StringTag tag) {
        Triad.Value value = dictionary.get(tag);
        if (value instanceof Value8) {
            return ((Value8) value).value;
        } else {
            return 0;
        }
    }

    protected ByteArray getBinaryValue(StringTag tag) {
        return dictionary.get(tag);
    }

    @Override
    public String toString() {
        return dictionary.toString();
    }

    //
    //  Map
    //

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
        return dictionary.containsKey(key);
    }

    @Override
    public boolean containsValue(Object value) {
        return dictionary.containsValue(value);
    }

    @Override
    public Triad.Value get(Object key) {
        return dictionary.get(key);
    }

    @Override
    public Triad.Value put(Triad.Tag key, Triad.Value value) {
        throw new UnsupportedOperationException("immutable!");
    }

    @Override
    public Triad.Value remove(Object key) {
        throw new UnsupportedOperationException("immutable!");
    }

    @Override
    public void putAll(Map<? extends Triad.Tag, ? extends Triad.Value> m) {
        throw new UnsupportedOperationException("immutable!");
    }

    @Override
    public void clear() {
        throw new UnsupportedOperationException("immutable!");
    }

    @Override
    public Set<Triad.Tag> keySet() {
        return dictionary.keySet();
    }

    @Override
    public Collection<Triad.Value> values() {
        return dictionary.values();
    }

    @Override
    public Set<Entry<Triad.Tag, Triad.Value>> entrySet() {
        return dictionary.entrySet();
    }
}
