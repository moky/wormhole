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

//! require 'ship.js'

(function (ns, sys) {
    'use strict';

    var Ship = ns.port.Ship;

    /**
     *  Incoming Ship
     *  ~~~~~~~~~~~~~
     */
    var Arrival = function () {};
    sys.Interface(Arrival, [Ship]);

    /**
     *  Data package can be sent as separated batches
     *
     * @param {Arrival} income - income ship carried with message fragment
     * @return {Arrival} new ship carried the whole data package
     */
    Arrival.prototype.assemble = function (income) {
        ns.assert(false, 'implement me!');
        return null;
    };

    //
    //  task states
    //

    /**
     *  Check whether task timeout
     *
     * @param {number} now - current time
     * @return {boolean} true on timeout
     */
    Arrival.prototype.isTimeout = function (now) {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Update expired time
     *
     * @param {number} now - current time
     */
    Arrival.prototype.touch = function (now) {
        ns.assert(false, 'implement me!');
    };

    //-------- namespace --------
    ns.port.Arrival = Arrival;

    ns.port.registers('Arrival');

})(StarTrek, MONKEY);
