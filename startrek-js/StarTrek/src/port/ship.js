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

    st.port.ShipStatus = Enum('ShipStatus', {

        //
        //  Departure Status
        //
        NEW:        (0x00),  // not try yet
        WAITING:    (0x01),  // sent, waiting for responses
        TIMEOUT:    (0x02),  // waiting to send again
        DONE:       (0x03),  // all fragments responded (or no need respond)
        FAILED:     (0x04),  // tried 3 times and missed response(s)

        //
        //  Arrival Status
        //
        ASSEMBLING: (0x10),  // waiting for more fragments
        EXPIRED:    (0x11)   // failed to received all fragments
    });
    var ShipStatus = st.port.ShipStatus;


    /**
     *  Star Ship
     *  ~~~~~~~~~
     *
     *  Container carrying data package
     */
    st.port.Ship = Interface(null, null);
    var Ship = st.port.Ship;

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


    /**
     *  Incoming Ship
     *  ~~~~~~~~~~~~~
     */
    st.port.Arrival = Interface(null, [Ship]);
    var Arrival = st.port.Arrival;

    /**
     *  Data package can be sent as separated batches
     *
     * @param {Arrival} income - income ship carried with message fragment
     * @return {Arrival} new ship carried the whole data package
     */
    Arrival.prototype.assemble = function (income) {};


    /**
     *  Departure Priority
     *  ~~~~~~~~~~~~~~~~~~
     */
    var DeparturePriority = {
        URGENT: -1,
        NORMAL:  0,
        SLOWER:  1
    };

    /**
     *  Outgoing Ship
     *  ~~~~~~~~~~~~~
     */
    st.port.Departure = Interface(null, [Ship]);
    var Departure = st.port.Departure;

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
