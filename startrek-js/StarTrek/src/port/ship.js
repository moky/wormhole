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

    var Interface = sys.type.Interface;
    var Enum      = sys.type.Enum;

    var ShipStatus = Enum(null, {
        //
        //  Arrival Status
        //
        ASSEMBLING: (0x00),  // waiting for more fragments
        EXPIRED:    (0x01),  // failed to received all fragments

        //
        //  Departure Status
        //
        NEW:        (0x10),  // not try yet
        WAITING:    (0x11),  // sent, waiting for responses
        TIMEOUT:    (0x12),  // waiting to send again
        DONE:       (0x13),  // all fragments responded (or no need respond)
        FAILED:     (0x14)   // tried 3 times and missed response(s)
    });

    /**
     *  Star Ship
     *  ~~~~~~~~~
     *
     *  Container carrying data package
     */
    var Ship = Interface(null, null);

    /**
     *  Get ID for this Ship
     *
     * @return SN
     */
    Ship.prototype.getSN = function () {};

    /**
     *  Update sent time
     *
     * @param {Date} now - current time
     */
    Ship.prototype.touch = function (now) {};

    /**
     *  Check ship state
     *
     * @param {Date} now - current time
     * @return {ShipStatus} current status
     */
    Ship.prototype.getStatus = function (now) {};

    //-------- namespace --------
    ns.port.Ship = Ship;
    ns.port.ShipStatus = ShipStatus;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;
    var Ship      = ns.port.Ship;

    /**
     *  Incoming Ship
     *  ~~~~~~~~~~~~~
     */
    var Arrival = Interface(null, [Ship]);

    /**
     *  Data package can be sent as separated batches
     *
     * @param {Arrival} income - income ship carried with message fragment
     * @return {Arrival} new ship carried the whole data package
     */
    Arrival.prototype.assemble = function (income) {};

    //-------- namespace --------
    ns.port.Arrival = Arrival;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Interface = sys.type.Interface;
    var Enum      = sys.type.Enum;
    var Ship      = ns.port.Ship;

    /**
     *  Departure Priority
     *  ~~~~~~~~~~~~~~~~~~
     */
    var DeparturePriority = Enum(null, {
        URGENT: -1,
        NORMAL:  0,
        SLOWER:  1
    });

    /**
     *  Outgoing Ship
     *  ~~~~~~~~~~~~~
     */
    var Departure = Interface(null, [Ship]);

    /**
     *  Task priority
     *
     * @return {int} default is 0, smaller is faster
     */
    Departure.prototype.getPriority = function () {};

    /**
     *  Get fragments to sent
     *
     * @return {Uint8Array[]} remaining separated data packages
     */
    Departure.prototype.getFragments = function () {};

    /**
     *  The received ship may carried a response for the departure
     *  if all fragments responded, means this task is finished.
     *
     * @param {Arrival} response - income ship carried with response
     * @return {boolean} true on task finished
     */
    Departure.prototype.checkResponse = function (response) {};

    /**
     *  Whether needs to wait for responses
     *
     * @return {boolean} false for disposable
     */
    Departure.prototype.isImportant = function () {};

    Departure.Priority = DeparturePriority;

    //-------- namespace --------
    ns.port.Departure = Departure;

})(StarTrek, MONKEY);
