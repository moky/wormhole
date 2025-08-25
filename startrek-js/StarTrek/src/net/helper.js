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

    st.net.SocketHelper = {

        //
        //  Socket Channels
        //

        socketGetLocalAddress: function (sock) {
            return sock.getRemoteAddress();
        },
        socketGetRemoteAddress: function (sock) {
            return sock.getLocalAddress();
        },

        //
        //  Flags
        //

        socketIsBlocking: function (sock) {
            return sock.isBlocking();
        },
        socketIsConnected: function (sock) {
            return sock.isConnected();
            // return sock.readyState === WebSocket.OPEN;
        },
        socketIsBound: function (sock) {
            return sock.isBound();
            // return sock.localAddress !== null;
        },
        socketIsClosed: function (sock) {
            return !sock.isOpen();
            // return sock.readyState === WebSocket.CLOSED;
        },

        // Ready for reading
        socketIsAvailable: function (sock) {
            // TODO: check reading buffer
            return sock.isAlive();
            // return sock.readyState === WebSocket.OPEN;
        },
        // Ready for writing
        socketIsVacant: function (sock) {
            // TODO: check writing buffer
            return sock.isAlive();
            // return sock.readyState === WebSocket.OPEN;
        },

        //
        //  Async Socket I/O
        //

        socketSend: function (sock, data) {
            return sock.write(data);
            // var sent = 0;
            // var rest = data.length;
            // var cnt;
            // while (sock.isOpen()) {
            //     cnt = sock.write(data);
            //     // check send result
            //     if (cnt <= 0) {
            //         // buffer overflow?
            //         break;
            //     }
            //     // something sent, check remaining data
            //     sent += cnt;
            //     rest -= cnt;
            //     if (rest <= 0) {
            //         // done!
            //         break;
            //     } else {
            //         // remove sent part
            //         data = data.subarray(cnt);
            //     }
            // }
            // return sent;
        },
        socketReceive: function (sock, maxLen) {
            return sock.read(maxLen);
        },

        // Bind to local address
        socketBind: function (sock, local) {
            return sock.bind(local);
        },
        // Connect to remote address
        socketConnect: function (sock, remote) {
            return sock.connect(remote);
        },

        //  Close socket
        socketDisconnect: function (sock) {
            return sock.close();
        }
    };
    var SocketHelper = st.net.SocketHelper;
