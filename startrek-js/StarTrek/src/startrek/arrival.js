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

//! require 'port/arrival.js'

(function (ns, sys) {
    'use strict';

    var Class      = sys.type.Class;
    var BaseObject = sys.type.BaseObject;
    var Arrival    = ns.port.Arrival;
    var ShipStatus = ns.port.ShipStatus;

    /**
     *  Arrival Ship
     *  ~~~~~~~~~~~~
     *
     * @param {Date} now
     */
    var ArrivalShip = function (now) {
        BaseObject.call(this);
        if (!now) {
            now = new Date();
        }
        this.__expired = now.getTime() + ArrivalShip.EXPIRED;
    };
    Class(ArrivalShip, BaseObject, [Arrival], null);

    /**
     *  Arrival task will be expired after 5 minutes
     *  if still not completed.
     */
    ArrivalShip.EXPIRES = 300 * 1000;  // milliseconds

    // Override
    ArrivalShip.prototype.touch = function (now) {
        // update expired time
        this.__expired = now.getTime() + ArrivalShip.EXPIRES;
    };

    // Override
    ArrivalShip.prototype.getStatus = function (now) {
        if (now.getTime() > this.__expired) {
            return ShipStatus.EXPIRED;
        } else {
            return ShipStatus.ASSEMBLING;
        }
    };

    //-------- namespace --------
    ns.ArrivalShip = ArrivalShip;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Class      = sys.type.Class;
    var HashSet    = sys.type.HashSet;
    var ShipStatus = ns.port.ShipStatus;

    /**
     *  Memory cache for Arrivals
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    var ArrivalHall = function () {
        Object.call(this);
        this.__arrivals = new HashSet();  // Set<Arrival>
        this.__arrival_map = {};          // SN => Arrival
        this.__finished_times = {};       // SN => Date
    };
    Class(ArrivalHall, Object, null, null);

    /**
     *  Check received ship for completed package
     *
     * @param {Arrival|Ship} income - received ship carrying data package (fragment)
     * @return {Arrival|Ship} ship carrying completed data package
     */
    ArrivalHall.prototype.assembleArrival = function (income) {
        // 1. check ship ID (SN)
        var sn = income.getSN();
        if (!sn) {
            // separated package ship must have SN for assembling
            // we consider it to be a ship carrying a whole package here
            return income;
        }
        // 2. check cached ship
        var completed;  // Arrival
        var cached = this.__arrival_map[sn];
        if (cached) {
            // 3. cached ship found, try assembling (insert as fragment)
            //    to check whether all fragments received
            completed = cached.assemble(income);
            if (completed) {
                // all fragments received, remove cached ship
                this.__arrivals.remove(cached);
                delete this.__arrival_map[sn];
                // mark finished time
                this.__finished_times[sn] = new Date();
            } else {
                // it's not completed yet, update expired time
                // and wait for more fragments.
                cached.touch(new Date());
            }
        } else {
            // check whether the task has already finished
            var time = this.__finished_times[sn];
            if (time) {
                // task already finished
                return null;
            }
            // 3. new arrival, try assembling to check whether a fragment
            completed = income.assemble(income);
            if (!completed) {
                // it's a fragment, waiting for more fragments
                this.__arrivals.add(income);
                this.__arrival_map[sn] = income;
                //income.touch(new Date());
            }
            // else, it's a completed package
        }
        return completed;
    };

    /**
     *  Clear all expired tasks
     */
    ArrivalHall.prototype.purge = function (now) {
        if (!now) {
            now = new Date();
        }
        var count = 0;
        // 1. seeking expired tasks
        var ship;
        var sn;
        var arrivals = this.__arrivals.toArray();  // copy
        for (var i = arrivals.length - 1; i >= 0; --i) {
            ship = arrivals[i];
            if (ship.getStatus(now) === ShipStatus.EXPIRED) {
                // remove mapping with SN
                sn = ship.getSN();
                if (sn) {
                    delete this.__arrival_map[sn];
                    // TODO: callback?
                }
                ++count;
                // task expired
                this.__arrivals.remove(ship);
            }
        }
        // 2. seeking neglected finished times
        var ago = now.getTime() - 3600 * 1000;
        var when;  // Date
        var keys = Object.keys(this.__finished_times);
        for (var j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__finished_times[sn];
            if (!when || when.getTime() < ago) {
                // long time ago
                delete this.__finished_times[sn];
                // // remove mapping with SN
                // delete this.__arrival_map[sn];
            }
        }
        return count;
    };

    //-------- namespace --------
    ns.ArrivalHall = ArrivalHall;

})(StarTrek, MONKEY);
