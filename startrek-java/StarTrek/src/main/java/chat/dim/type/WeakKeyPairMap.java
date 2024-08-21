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

import java.util.Map;
import java.util.WeakHashMap;

public abstract class WeakKeyPairMap<K, V> implements KeyPairMap<K, V> {

    private final K defaultKey;

    // because the remote address will always different to local address, so
    // we shared the same map for all directions here:
    //    mapping: (remote, local) => Connection
    //    mapping: (remote, null) => Connection
    //    mapping: (local, null) => Connection
    private final Map<K, Map<K, V>> map = new WeakHashMap<>();

    protected WeakKeyPairMap(K any) {
        super();
        defaultKey = any;
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
        V value;
        if (key2 != null) {
            // mapping: (remote, local) => Connection
            value = table.get(key2);
            if (value != null) {
                return value;
            }
            // take any Connection connected to remote
            return table.get(defaultKey);
        }
        // mapping: (remote, null) => Connection
        // mapping: (local, null) => Connection
        value = table.get(defaultKey);
        if (value != null) {
            // take the value with empty key2
            return value;
        }
        // take any Connection connected to remote / bound to local
        for (V v : table.values()) {
            if (v != null) {
                return v;
            }
        }
        return null;
    }

    @Override
    public V set(K remote, K local, V value) {
        // create indexes with key pair (remote, local)
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
            if (value == null) {
                return table.remove(key2);
            } else {
                return table.put(key2, value);
            }
        } else if (value != null) {
            table = new WeakMap<>();
            table.put(key2, value);
            map.put(key1, table);
        }
        return null;
    }

    @Override
    public V remove(K remote, K local, V value) {
        // remove indexes with key pair (remote, local)
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
            return value;
        }
        V old = table.remove(key2);
        if (table.isEmpty()) {
            map.remove(key1);
        }
        return old == null ? value : old;
    }

}
