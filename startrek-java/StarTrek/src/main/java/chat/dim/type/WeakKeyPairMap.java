/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.type;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.WeakHashMap;

public abstract class WeakKeyPairMap<K, V> implements KeyPairMap<K, V> {

    private final K defaultKey;

    // because the remote address will always different to local address, so
    // we shared the same map for all directions here:
    //    mapping: (remote, local) => Connection
    //    mapping: (remote, null) => Connection
    //    mapping: (local, null) => Connection
    private final Map<K, Map<K, V>> map = new HashMap<>();

    public WeakKeyPairMap(K any) {
        super();
        defaultKey = any;
    }

    @Override
    public void put(K remote, K local, V value) {
        // create indexes for this connection
        K key1, key2;
        if (remote == null) {
            assert local != null : "local & remote addresses should not empty at the same time";
            key1 = local;
            key2 = defaultKey;
        } else if (local == null) {
            key1 = remote;
            key2 = defaultKey;
        } else {
            key1 = remote;
            key2 = local;
        }
        Map<K, V> table = map.get(key1);
        if (table == null) {
            table = new WeakHashMap<>();
            table.put(key2, value);
            map.put(key1, table);
        } else {
            table.put(key2, value);
        }
    }

    @Override
    public V get(K remote, K local) {
        K key1, key2;
        if (remote == null) {
            assert local != null : "local & remote addresses should not empty at the same time";
            key1 = local;
            key2 = null;
        } else {
            key1 = remote;
            key2 = local;
        }
        Map<K, V> table = map.get(key1);
        if (table == null) {
            return null;
        }
        if (key2 != null) {
            // mapping: (remote, local) => Connection
            return table.get(key2);
        }
        // mapping: (remote, null) => Connection
        // mapping: (local, null) => Connection
        V value = table.get(defaultKey);
        if (value == null) {
            // take the first value if exists
            Iterator<V> it = table.values().iterator();
            return it.hasNext() ? it.next() : null;
        } else {
            // take the value with empty key2
            return value;
        }
    }

    @Override
    public void remove(K remote, K local, V value) {
        // remove indexes for this connection
        K key1, key2;
        if (remote == null) {
            assert local != null : "local & remote addresses should not empty at the same time";
            key1 = local;
            key2 = defaultKey;
        } else if (local == null) {
            key1 = remote;
            key2 = defaultKey;
        } else {
            key1 = remote;
            key2 = local;
        }
        Map<K, V> table = map.get(key1);
        if (table != null) {
            table.remove(key2);
        }
    }
}
