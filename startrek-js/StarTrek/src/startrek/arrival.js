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

//! require 'port/arrival.js'

    /**
     *  Arrival Ship
     *  ~~~~~~~~~~~~
     *
     * @param {Date} now
     */
    st.ArrivalShip = function (now) {
        BaseObject.call(this);
        if (!now) {
            now = new Date();
        }
        this.__expired = ArrivalShip.EXPIRES.addTo(now);
    };
    var ArrivalShip = st.ArrivalShip;

    Class(ArrivalShip, BaseObject, [Arrival]);

    /**
     *  Arrival task will be expired after 5 minutes
     *  if still not completed.
     */
    ArrivalShip.EXPIRES = Duration.ofMinutes(5);

    // Override
    ArrivalShip.prototype.touch = function (now) {
        // update expired time
        this.__expired = ArrivalShip.EXPIRES.addTo(now);
    };

    // Override
    ArrivalShip.prototype.getStatus = function (now) {
        if (now.getTime() > this.__expired.getTime()) {
            return ShipStatus.EXPIRED;
        } else {
            return ShipStatus.ASSEMBLING;
        }
    };


    /**
     *  Memory cache for Arrivals
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    st.ArrivalHall = function () {
        BaseObject.call(this);
        this.__arrivals = new HashSet();  // Set<Arrival>
        this.__arrival_map = {};          // SN => Arrival
        this.__finished_times = {};       // SN => Date
    };
    var ArrivalHall = st.ArrivalHall;

    Class(ArrivalHall, BaseObject, null);

    /**
     *  Check received ship for completed package
     *
     * @param {st.port.Arrival|st.port.Ship} income - received ship carrying data package (fragment)
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
        var ago = Duration.ofMinutes(60).subtractFrom(now);
        ago = ago.getTime();
        var finished_times = this.__finished_times;
        Mapper.forEach(finished_times, function (sn, when) {
            if (!when || when.getTime() < ago) {
                // long time ago
                delete finished_times[sn];
                // // remove mapping with SN
                // delete this.__arrival_map[sn];
            }
            return false;
        });
        return count;
    };
