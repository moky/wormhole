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

//! require 'arrival.js'
//! require 'departure.js'

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var ArrivalHall = ns.ArrivalHall;
    var DepartureHall = ns.DepartureHall;

    var Dock = function () {
        Object.call(this);
        this.__arrivalHall = this.createArrivalHall();
        this.__departureHall = this.createDepartureHall();
    };
    Class(Dock, Object, null, null);

    // protected: override for user-customized hall
    Dock.prototype.createArrivalHall = function () {
        return new ArrivalHall();
    };

    // protected: override for user-customized hall
    Dock.prototype.createDepartureHall = function () {
        return new DepartureHall();
    };

    /**
     * Check received ship for completed package
     *
     * @param {Arrival|Ship} income - received ship carrying data package (fragment)
     * @return {Arrival|Ship} ship carrying completed data package
     */
    Dock.prototype.assembleArrival = function (income) {
        // check fragment from income ship,
        // return a ship with completed package if all fragments received
        return this.__arrivalHall.assembleArrival(income);
    };

    /**
     *  Add outgoing ship to the waiting queue
     *
     * @param {Departure|Ship} outgo - departure task
     * @return {boolean} false on duplicated
     */
    Dock.prototype.addDeparture = function (outgo) {
        return this.__departureHall.addDeparture(outgo);
    };

    /**
     *  Check response from incoming ship
     *
     * @param {Arrival|Ship} response - incoming ship with SN
     * @return {DepartureShip} finished task
     */
    Dock.prototype.checkResponse = function (response) {
        // check departure tasks with SN
        // remove package/fragment if matched (check page index for fragments too)
        return this.__departureHall.checkResponse(response);
    };

    /**
     *  Get next new/timeout task
     *
     * @param {number} now - current time
     * @return {Departure|Ship} departure task
     */
    Dock.prototype.getNextDeparture = function (now) {
        // this will be remove from the queue,
        // if needs retry, the caller should append it back
        return this.__departureHall.getNextDeparture(now);
    };

    /**
     * Clear all expired tasks
     */
    Dock.prototype.purge = function () {
        this.__arrivalHall.purge();
        this.__departureHall.purge();
    };

    //-------- namespace --------
    ns.Dock = Dock;

})(StarTrek, MONKEY);
