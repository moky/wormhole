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

//! require 'address.js'
//! require 'hash.js'

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var InetSocketAddress = ns.type.InetSocketAddress;
    var HashKeyPairMap = ns.type.HashKeyPairMap;

    var AnyAddress = new InetSocketAddress('0.0.0.0', 0);

    var AddressPairMap = function () {
        HashKeyPairMap.call(this, AnyAddress);
    };
    Class(AddressPairMap, HashKeyPairMap, null, null);

    AddressPairMap.AnyAddress = AnyAddress;

    //-------- namespace --------
    ns.type.AddressPairMap = AddressPairMap;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var BaseObject = sys.type.BaseObject;

    /**
     *  Object with remote & local addresses
     *
     * @param {SocketAddress} remote
     * @param {SocketAddress} local
     */
    var AddressPairObject = function (remote, local) {
        BaseObject.call(this);
        // protected
        this.remoteAddress = remote;
        this.localAddress = local;
    };
    Class(AddressPairObject, BaseObject, null, null);

    AddressPairObject.prototype.getRemoteAddress = function () {
        return this.remoteAddress;
    };

    AddressPairObject.prototype.getLocalAddress = function () {
        return this.localAddress;
    };

    // Override
    AddressPairObject.prototype.equals = function (other) {
        if (!other) {
            return !this.remoteAddress && !this.localAddress;
        } else if (other === this) {
            return true;
        } else if (other instanceof AddressPairObject) {
            return address_equals(other.getRemoteAddress(), this.remoteAddress) &&
                address_equals(other.getLocalAddress(), this.localAddress);
        } else {
            return false;
        }
    };

    // Override
    AddressPairObject.prototype.valueOf = function () {
        return desc.call(this);
    };

    // Override
    AddressPairObject.prototype.toString = function () {
        return desc.call(this);
    };

    var address_equals = function (address1, address2) {
        if (address1) {
            return address1.equals(address2);
        } else {
            return !address2;
        }
    };

    var desc = function () {
        var cname = this.constructor.name;
        var remote = this.getRemoteAddress();
        var local = this.getLocalAddress();
        if (remote) {
            remote = remote.toString();
        }
        if (local) {
            local = local.toString();
        }
        return '<' + cname + ' remote="' + remote + '" local="' + local + '" />';
    };

    //-------- namespace --------
    ns.type.AddressPairObject = AddressPairObject;

})(StarTrek, MONKEY);
