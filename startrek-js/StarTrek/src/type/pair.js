'use strict';
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

//! require 'namespace.js'

    st.type.Pair = function (a, b) {
        BaseObject.call(this);
        this.a = a;
        this.b = b;
    };
    var Pair = st.type.Pair;

    Class(Pair, BaseObject, null, null);

    Pair.prototype.equals = function (other) {
        if (other instanceof Pair) {
            return object_equals(this.a, other.a) && object_equals(this.b, other.b);
        }
        return false;
    };


    /**
     *  Key Pair Map
     *  ~~~~~~~~~~~~
     */
    st.type.PairMap = Interface(null, null);
    var PairMap = st.type.PairMap;

    /**
     *  Get all mapped values
     *
     * @return {[]} all values
     */
    PairMap.prototype.items = function () {};

    /**
     *  Get value by key pair (remote, local)
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     * @return {*} mapped value
     */
    PairMap.prototype.get = function (remote, local) {};

    /**
     *  Set value by key pair (remote, local)
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     * @param {*} value  - mapping value
     */
    PairMap.prototype.set = function (remote, local, value) {};

    /**
     *  Remove mapping by key pair (remote, local)
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     * @param {*} value  - mapped value (Optional)
     * @return {*} removed value
     */
    PairMap.prototype.remove = function (remote, local, value) {};
