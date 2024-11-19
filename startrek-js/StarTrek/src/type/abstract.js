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

    var PairMap = ns.type.PairMap;

    /**
     *  Hash Key Pair Map
     *  ~~~~~~~~~~~~~~~~~
     */
    var AbstractPairMap = function (any) {
        Object.call(this);
        // default key
        this.__default = any;
        // because the remote address will always different to local address, so
        // we shared the same map for all directions here:
        //    mapping: (remote, local) => Connection
        //    mapping: (remote, null) => Connection
        //    mapping: (local, null) => Connection
        this.__map = {};
    };
    Class(AbstractPairMap, Object, [PairMap], null);

    // Override
    AbstractPairMap.prototype.get = function (remote, local) {
        var key_pair = get_keys(remote, local, null);
        var key1 = key_pair[0];
        var key2 = key_pair[1];
        var table = this.__map[key1];
        if (!table) {
            return null;
        }
        var value;
        if (key2) {
            // mapping: (remote, local) => Connection
            value = table[key2];
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
        var addresses = Object.keys(table);
        for (var i = 0; i < addresses.length; ++i) {
            value = table[addresses[i]];
            if (value) {
                return value;
            }
        }
        return null;
    };

    // Override
    AbstractPairMap.prototype.set = function (remote, local, value) {
        // create indexes with key pair (remote, local)
        var key_pair = get_keys(remote, local, this.__default);
        var key1 = key_pair[0];
        var key2 = key_pair[1];
        var table = this.__map[key1];
        var old = null;
        if (table) {
            old = table[key2];
            if (value) {
                table[key2] = value;
            } else if (old) {
                delete table[key2];
            }
        } else if (value) {
            table = {};
            table[key2] = value;
            this.__map[key1] = table;
        }
        return old;
    };

    // Override
    AbstractPairMap.prototype.remove = function (remote, local, value) {
        // remove indexes with key pair (remote, local)
        var key_pair = get_keys(remote, local, this.__default);
        var key1 = key_pair[0];
        var key2 = key_pair[1];
        var table = this.__map[key1];
        if (!table) {
            return null;
        }
        var old = table[key2];
        if (old) {
            // old value found,
            // remove key2 from table
            delete table[key2];
            if (Object.keys(table).length === 0) {
                // table empty,
                // remove table from map
                delete this.__map[key1];
            }
        }
        return old ? old : value;
    };

    var get_keys = function (remote, local, any) {
        if (!remote) {
            return [local, any]
        } else if (!local) {
            return [remote, any]
        } else {
            return [remote, local]
        }
    };

    //-------- namespace --------
    ns.type.AbstractPairMap = AbstractPairMap;

})(StarTrek, MONKEY);
