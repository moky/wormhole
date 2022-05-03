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

//! require <crypto.js>

if (typeof StarTrek !== 'object') {
    StarTrek = new MONKEY.Namespace();
}

(function (ns, sys) {
    'use strict';

    if (typeof ns.assert !== 'function') {
        ns.assert = console.assert;
    }

    //-------- namespace --------
    if (typeof ns.net !== 'object') {
        ns.net = new sys.Namespace();
    }
    if (typeof ns.port !== 'object') {
        ns.port = new sys.Namespace();
    }
    if (typeof ns.socket !== 'object') {
        ns.socket = new sys.Namespace();
    }

    ns.registers('net');
    ns.registers('port');
    ns.registers('socket');

})(StarTrek, MONKEY);

(function (ns) {
    'use strict';

    //-------- namespace --------
    if (typeof ns.type !== 'object') {
        ns.type = new ns.Namespace();
    }

    ns.registers('type');

})(MONKEY);
