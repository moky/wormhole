/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2022 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2022 Albert Moky
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
package chat.dim.type;

import java.lang.ref.WeakReference;
import java.util.Collection;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

/**
 *  Weak Key & Value Map
 *
 * @param <K> Key type
 * @param <V> Value type
 */
public class WeakMap<K, V> implements Map<K, V> {

    private final Map<K, WeakReference<V>> map = new WeakHashMap<>();

    @Override
    public int size() {
        return map.size();
    }

    @Override
    public boolean isEmpty() {
        return map.isEmpty();
    }

    @Override
    public boolean containsKey(Object key) {
        return map.containsKey(key);
    }

    @Override
    public boolean containsValue(Object value) {
        V item;
        for (WeakReference<V> ref : map.values()) {
            item = ref == null ? null : ref.get();
            if (item != null && item.equals(value)) {
                return true;
            }
        }
        return false;
    }

    @Override
    public V get(Object key) {
        WeakReference<V> ref = map.get(key);
        return ref == null ? null : ref.get();
    }

    @Override
    public V put(K key, V value) {
        assert value != null : "value should not be empty";
        WeakReference<V> ref = map.get(key);
        map.put(key, new WeakReference<>(value));
        return ref == null ? null : ref.get();
    }

    @Override
    public V remove(Object key) {
        WeakReference<V> ref = map.remove(key);
        return ref == null ? null : ref.get();
    }

    @Override
    public void putAll(Map<? extends K, ? extends V> m) {
        Iterator<? extends Map.Entry<? extends K, ? extends V>> iterator = m.entrySet().iterator();
        Map.Entry<? extends K, ? extends V> entry;
        K key;
        V value;
        while (iterator.hasNext()) {
            entry = iterator.next();
            key = entry.getKey();
            value = entry.getValue();
            if (value != null) {
                put(key, value);
            }
        }
    }

    @Override
    public void clear() {
        map.clear();
    }

    @Override
    public Set<K> keySet() {
        return map.keySet();
    }

    @Override
    public Collection<V> values() {
        Collection<V> objects = new HashSet<>();
        Collection<WeakReference<V>> references = map.values();
        V val;
        for (WeakReference<V> ref : references) {
            val = ref == null ? null : ref.get();
            if (val != null) {
                objects.add(val);
            }
        }
        return objects;
    }

    @Override
    public Set<Map.Entry<K, V>> entrySet() {
        Set<Map.Entry<K, V>> targetSet = new HashSet<>();
        Iterator<Map.Entry<K, WeakReference<V>>> iterator = map.entrySet().iterator();
        Map.Entry<K, WeakReference<V>> entry;
        while (iterator.hasNext()) {
            entry = iterator.next();
            targetSet.add(new Entry<>(entry));
        }
        return targetSet;
    }

    private static class Entry<K, V> implements Map.Entry<K, V> {

        private final Map.Entry<K, WeakReference<V>> entry;

        Entry(Map.Entry<K, WeakReference<V>> e) {
            super();
            entry = e;
        }

        @Override
        public K getKey() {
            return entry.getKey();
        }

        @Override
        public V getValue() {
            WeakReference<V> ref = entry.getValue();
            return ref == null ? null : ref.get();
        }

        @Override
        public V setValue(V value) {
            WeakReference<V> ref = entry.getValue();
            if (value == null) {
                entry.setValue(null);
            } else {
                entry.setValue(new WeakReference<>(value));
            }
            return ref == null ? null : ref.get();
        }
    }
}
