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

import java.util.HashSet;
import java.util.Set;

public class HashKeyPairMap<K, V> extends WeakKeyPairMap<K, V> {

    private final Set<V> cachedValues = new HashSet<>();

    public HashKeyPairMap(K any) {
        super(any);
    }

    @Override
    public Set<V> allValues() {
        return new HashSet<>(cachedValues);
    }

    @Override
    public void put(K remote, K local, V value) {
        if (value != null) {
            // the caller may create different values with same pair (remote, local)
            // so here we should try to remove it first to make sure it's clean
            cachedValues.remove(value);
            // cache it
            cachedValues.add(value);
        }
        // create indexes
        super.put(remote, local, value);
    }

    @Override
    public V remove(K remote, K local, V value) {
        // remove indexes
        V old = super.remove(remote, local, value);
        if (old != null) {
            cachedValues.remove(old);
        }
        // clear cached value
        if (value != null && value != old) {
            cachedValues.remove(value);
        }
        return old == null ? value : old;
    }
}
