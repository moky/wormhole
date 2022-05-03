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
     *  Outgoing Ship
     *  ~~~~~~~~~~~~~
     */
    var Departure = function () {};
    sys.Interface(Departure, [Ship]);

    /**
     *  Departure Priority
     *  ~~~~~~~~~~~~~~~~~~
     */
    var DeparturePriority = sys.type.Enum(null, {
        URGENT: -1,
        NORMAL:  0,
        SLOWER:  1
    });

    /**
     *  Task priority
     *
     * @return {int} default is 0, smaller is faster
     */
    Departure.prototype.getPriority = function () {
        ns.assert(false, 'implement me!');
        return 0;
    };

    /**
     *  Get fragments to sent
     *
     * @return {Uint8Array[]} remaining separated data packages
     */
    Departure.prototype.getFragments = function () {
        ns.assert(false, 'implement me!');
        return null;
    };

    /**
     *  The received ship may carried a response for the departure
     *  if all fragments responded, means this task is finished.
     *
     * @param {Arrival} response - income ship carried with response
     * @return {boolean} true on task finished
     */
    Departure.prototype.checkResponse = function (response) {
        ns.assert(false, 'implement me!');
        return false;
    };

    //
    //  task states
    //

    /**
     *  Check whether it's a new task
     *
     * @return {boolean} true for new task
     */
    Departure.prototype.isNew = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Check whether it can be removed immediately
     *
     * @return {boolean} true for task needs no response
     */
    Departure.prototype.isDisposable = function () {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Check whether task needs retry
     *
     * @param {number} now - current time
     * @return {boolean} true on timeout
     */
    Departure.prototype.isTimeout = function (now) {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Check whether task's response(s) missed
     *
     * @param {number} now - current time
     * @return {boolean} true on failed
     */
    Departure.prototype.isFailed = function (now) {
        ns.assert(false, 'implement me!');
        return false;
    };

    /**
     *  Update expired time
     *
     * @param {number} now - current time
     */
    Departure.prototype.touch = function (now) {
        ns.assert(false, 'implement me!');
    };

    Departure.Priority = DeparturePriority;

    //-------- namespace --------
    ns.port.Departure = Departure;

    ns.port.registers('Departure');

})(StarTrek, MONKEY);
