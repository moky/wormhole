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

    st.type.SocketAddress = Interface(null, [Stringer]);
    var SocketAddress = st.type.SocketAddress;

    SocketAddress.prototype.getHost = function () {};

    SocketAddress.prototype.getPort = function () {};

    /**
     *  IP Socket Address
     *  ~~~~~~~~~~~~~~~~~
     *
     * @param {String} host
     * @param {Number} port
     */
    st.type.InetSocketAddress = function (host, port) {
        ConstantString.call(this, '(' + host + ':' + port + ')');
        this.__host = host;
        this.__port = port;
    };
    var InetSocketAddress = st.type.InetSocketAddress

    Class(InetSocketAddress, ConstantString, [SocketAddress]);

    // Override
    InetSocketAddress.prototype.getHost = function () {
        return this.__host;
    };

    // Override
    InetSocketAddress.prototype.getPort = function () {
        return this.__port;
    };


    st.type.AnyAddress = new InetSocketAddress('0.0.0.0', 0);
    var AnyAddress = st.type.AnyAddress;
