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

    var Class = sys.type.Class;

    var KeyPairMap = ns.type.KeyPairMap;

    var HashKeyPairMap = function (any) {
        Object.call(this);
        // default key
        this.__default = any;
        // because the remote address will always different to local address, so
        // we shared the same map for all directions here:
        //    mapping: (remote, local) => Connection
        //    mapping: (remote, null) => Connection
        //    mapping: (local, null) => Connection
        this.__map = {};
        // cached values
        this.__values = [];
    };
    Class(HashKeyPairMap, Object, [KeyPairMap], null);

    // Override
    HashKeyPairMap.prototype.values = function () {
        return this.__values;
    };

    // Override
    HashKeyPairMap.prototype.get = function (remote, local) {
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map[keys[0]];
        if (!table) {
            return null;
        }
        var value;
        if (keys[1]) {
            // mapping: (remote, local) => Connection
            value = table[keys[1]];
            if (value) {
                return value;
            }
            // take any Connection connected to remote
            return table[this.__default];
        }
        // mapping: (remote, null) => Connection
        // mapping: (local, null) => Connection
        value = table[this.__default];
        if (value) {
            // take the value with empty key2
            return value;
        }
        // take any Connection connected to remote / bound to local
        var allKeys = Object.keys(table);
        for (var i = 0; i < allKeys.length; ++i) {
            value = table[allKeys[i]];
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
        var table = this.__map[keys[0]];
        if (table) {
            if (!value) {
                delete table[keys[1]];
            } else {
                table[keys[1]] = value;
            }
        } else if (value) {
            table = {};
            table[keys[1]] = value;
            this.__map[keys[0]] = table;
        }
    };

    // Override
    HashKeyPairMap.prototype.remove = function (remote, local, value) {
        // remove indexes with key pair (remote, local)
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map[keys[0]];
        var old = null;
        if (table) {
            old = table[keys[1]];
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
            return [localAddress, defaultAddress]
        } else if (!localAddress) {
            return [remoteAddress, defaultAddress]
        } else {
            return [remoteAddress, localAddress]
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

})(StarTrek, MONKEY);
