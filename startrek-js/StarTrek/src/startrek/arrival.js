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

    var Arrival = ns.port.Arrival;

    /**
     *  Arrival Ship
     *  ~~~~~~~~~~~~
     *
     * @param {number} now
     */
    var ArrivalShip = function (now) {
        Object.call(this);
        if (!now) {
            now = (new Date()).getTime();
        }
        this.__expired = now + ArrivalShip.EXPIRED;
    };
    sys.Class(ArrivalShip, Object, [Arrival], null);

    /**
     *  Arrival task will be expired after 10 minutes
     *  if still not completed.
     */
    ArrivalShip.EXPIRES = 600 * 1000;  // milliseconds

    // Override
    ArrivalShip.prototype.isTimeout = function (now) {
        return now > this.__expired;
    };

    // Override
    ArrivalShip.prototype.touch = function (now) {
        this.__expired = now + ArrivalShip.EXPIRES;
    };

    //-------- namespace --------
    ns.ArrivalShip = ArrivalShip;

    ns.registers('ArrivalShip');

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Arrays = sys.type.Arrays;
    var Dictionary = sys.type.Dictionary;

    var ArrivalHall = function () {
        Object.call(this);
        this.__arrivals = [];           // Arrival[]
        this.__amap = new Dictionary(); // ID => Arrival
        this.__aft = new Dictionary();  // ID => timestamp
    }
    sys.Class(ArrivalHall, Object, null, null);

    /**
     *  Check received ship for completed package
     *
     * @param {Arrival|Ship} income - received ship carrying data package (fragment)
     * @return {Arrival|Ship} ship carrying completed data package
     */
    ArrivalHall.prototype.assembleArrival = function (income) {
        // check ship ID (SN)
        var sn = income.getSN();
        if (!sn) {
            // separated package ship must have SN for assembling
            // we consider it to be a ship carrying a whole package here
            return income;
        }
        // check whether the task has already finished
        var time = this.__aft.getValue(sn);
        if (time && time > 0) {
            // task already finished
            return null;
        }
        var task = this.__amap.getValue(sn);
        if (!task) {
            // new arrival, try assembling to check whether a fragment
            task = income.assemble(income);
            if (!task) {
                // it's a fragment, waiting for more fragments
                this.__arrivals.push(income);
                this.__amap.setValue(sn, income);
                return null;
            } else {
                // it's a completed package
                return task;
            }
        }
        // insert as fragment
        var completed = task.assemble(income);
        if (!completed) {
            // not completed yet, update expired time
            // and wait for more fragments.
            task.touch((new Date()).getTime());
            return null;
        }
        // all fragments received, remove this task
        Arrays.remove(this.__arrivals, task);
        this.__amap.removeValue(sn);
        // mark finished time
        this.__aft.setValue(sn, (new Date()).getTime());
        return completed;
    };

    /**
     *  Clear all expired tasks
     */
    ArrivalHall.prototype.purge = function () {
        var now = (new Date()).getTime();
        // 1. seeking expired tasks
        var ship;
        for (var i = this.__arrivals.length - 1; i >= 0; --i) {
            ship = this.__arrivals[i];
            if (ship.isTimeout(now)) {
                // task expired
                this.__arrivals.splice(i, 1);
                // remove mapping with SN
                this.__amap.removeValue(ship.getSN());
                // TODO: callback?
            }
        }
        // 2. seeking neglected finished times
        var ago = now - 3600;
        var keys = this.__aft.allKeys();
        var sn, when;
        for (var j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__aft.getValue(sn);
            if (!when || when < ago) {
                // long time ago
                this.__aft.removeValue(sn);
                // remove mapping with SN
                this.__amap.removeValue(sn);
            }
        }
    };

    //-------- namespace --------
    ns.ArrivalHall = ArrivalHall;

    ns.registers('ArrivalHall');

})(StarTrek, MONKEY);
