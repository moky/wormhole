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

//! require 'namespace.js'

(function (ns, sys) {
    'use strict';

    var KeyPairMap = function () {};
    sys.Interface(KeyPairMap, null);

    /**
     *  Get all mapped values
     *
     * @return {[]} values
     */
    KeyPairMap.prototype.allValues = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    /**
     *  Get value by key pair (remote, local)
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     * @return {*} mapped value
     */
    KeyPairMap.prototype.get = function (remote, local) {
        ns.assert(false, 'implement me!');
        return null;
    };

    /**
     *  Set value by key pair (remote, local)
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     * @param {*} value  - mapping value
     */
    KeyPairMap.prototype.set = function (remote, local, value) {
        ns.assert(false, 'implement me!');
        return null;
    };

    /**
     *  Remove mapping by key pair (remote, local)
     *
     * @param {SocketAddress} remote - remote address
     * @param {SocketAddress} local  - local address
     * @param {*} value  - mapped value (Optional)
     * @return {*} removed value
     */
    KeyPairMap.prototype.remove = function (remote, local, value) {
        ns.assert(false, 'implement me!');
        return null;
    };

    //-------- namespace --------
    ns.type.KeyPairMap = KeyPairMap;

    ns.type.registers('KeyPairMap');

})(StarTrek, MONKEY);
