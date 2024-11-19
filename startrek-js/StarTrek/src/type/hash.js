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

//! require 'abstract.js'

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;
    var IObject   = sys.type.Object;
    var Class     = sys.type.Class;

    var AbstractPairMap = ns.type.AbstractPairMap;

    /**
     *  Hash Key Pair Map
     *  ~~~~~~~~~~~~~~~~~
     */
    var HashPairMap = function (any) {
        AbstractPairMap.call(this, any);
        this.__items = [];  // Set
    };
    Class(HashPairMap, AbstractPairMap, null, null);

    // Override
    HashPairMap.prototype.set = function (remote, local, value) {
        if (value) {
            // the caller may create different values with same pair (remote, local)
            // so here we should try to remove it first to make sure it's clean
            remove_item(this.__items, value);
            // cache it
            this.__items.push(value);
        }
        // create indexes with key pair (remote, local)
        var old = AbstractPairMap.prototype.set.call(this, remote, local, value);
        // clear replaced value
        if (old && !object_equals(old, value)) {
            remove_item(this.__items, old);
        }
        return old;
    };

    // Override
    HashPairMap.prototype.remove = function (remote, local, value) {
        // remove indexes with key pair (remote, local)
        var old = AbstractPairMap.prototype.remove.call(this, remote, local, value);
        if (old) {
            remove_item(this.__items, old);
        }
        // clear cached value
        if (value && !object_equals(value, old)) {
            remove_item(this.__items, value);
        }
        return old ? old : value;
    };

    var object_equals = function (a, b) {
        if (!a) {
            return !b;
        } else if (!b) {
            return false;
        } else if (a === b) {
            // same object
            return true;
        } else if (Interface.conforms(a, IObject)) {
            return a.equals(b);
        } else if (Interface.conforms(b, IObject)) {
            return b.equals(a);
        } else {
            return false;
        }
    };

    var remove_item = function (array, item) {
        for (var index = array.length - 1; index >= 0; --index) {
            if (object_equals(array[index], item)) {
                array.splice(index, 1);
            }
        }
    };

    //-------- namespace --------
    ns.type.HashPairMap = HashPairMap;

})(StarTrek, MONKEY);
