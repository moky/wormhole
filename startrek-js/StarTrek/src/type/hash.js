;
// license: https://mit-license.org
//
//  Star Trek: Interstellar Transport
//
//                               Written in 2022 by Moky <albert.moky@gmail.com>
//
// =============================================================================
// The MIT License (MIT)
//
// Copyright (c) 2022 Albert Moky
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// =============================================================================
//

//! require 'pair.js'

(function (ns, sys) {
    'use strict';

    var Dictionary = sys.type.Dictionary;
    var KeyPairMap = ns.type.KeyPairMap;

    var HashKeyPairMap = function (any) {
        Object.call(this);
        this.__default = any;
        this.__map = new Dictionary();
        this.__values = [];
    };
    sys.Class(HashKeyPairMap, Object, [KeyPairMap], null);

    // Override
    HashKeyPairMap.prototype.allValues = function () {
        return this.__values;
    };

    // Override
    HashKeyPairMap.prototype.get = function (remote, local) {
        var key1, key2;
        if (remote) {
            key1 = remote;
            key2 = local;
        } else {
            key1 = local;
            key2 = null;
        }
        var table = this.__map.getValue(key1);
        if (!table) {
            return null;
        }
        var value;
        if (key2) {
            // mapping: (remote, local) => Connection
            value = table.getValue(key2);
            if (value) {
                return value;
            }
            // take any Connection connected to remote
            return table.getValue(this.__default);
        }
        // mapping: (remote, null) => Connection
        // mapping: (local, null) => Connection
        value = table.getValue(this.__default);
        if (value) {
            // take the value with empty key2
            return value;
        }
        // take any Connection connected to remote / bound to local
        var allKeys = table.allKeys();
        for (var i = 0; i < allKeys.length; ++i) {
            value = table.getValue(allKeys[i]);
            if (value) {
                return value;
            }
        }
        return null;
    };

    // Override
    HashKeyPairMap.prototype.set = function (remote, local, value) {
        if (value) {
            // the caller may create different values with same pair (remote, local)
            // so here we should try to remove it first to make sure it's clean
            remove_item(this.__values, value);
            // cache it
            this.__values.push(value);
        }
        // create indexes with key pair (remote, local)
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map.getValue(keys.key1);
        if (table) {
            table.setValue(keys.key2, value);
        } else if (value) {
            table = new Dictionary();
            table.setValue(keys.key2, value);
            this.__map.setValue(keys.key1, table);
        }
    };

    // Override
    HashKeyPairMap.prototype.remove = function (remote, local, value) {
        // remove indexes with key pair (remote, local)
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map.getValue(keys.key1);
        var old = null;
        if (table) {
            old = table.removeValue(keys.key2);
            if (old) {
                remove_item(this.__values, old);
            }
        }
        // clear cached value
        if (value && value !== old) {
            remove_item(this.__values, value);
        }
        return old ? old : value;
    };

    var get_keys = function (remoteAddress, localAddress, defaultAddress) {
        if (!remoteAddress) {
            return {
                key1: localAddress,
                key2: defaultAddress
            }
        } else if (!localAddress) {
            return {
                key1: remoteAddress,
                key2: defaultAddress
            }
        } else {
            return {
                key1: remoteAddress,
                key2: localAddress
            }
        }
    };

    var remove_item = function (array, item) {
        var remote = item.getRemoteAddress();
        var local = item.getLocalAddress();
        var old;
        for (var index = array.length - 1; index >= 0; --index) {
            old = array[index];
            if (old === item) {
                // remove it
                array.splice(index, 1);
                continue;
            }
            // remove value(s) with same addresses too
            if (address_equals(old.getRemoteAddress(), remote) &&
                address_equals(old.getLocalAddress(), local)) {
                // addresses matched, remove it
                array.splice(index, 1);
            }
        }
    };
    var address_equals = function (address1, address2) {
        if (address1) {
            return address1.equals(address2);
        } else {
            return !address2;
        }
    };

    //-------- namespace --------
    ns.type.HashKeyPairMap = HashKeyPairMap;

    ns.type.registers('HashKeyPairMap');

})(StarTrek, MONKEY);
