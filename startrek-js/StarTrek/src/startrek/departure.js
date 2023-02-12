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

//! require 'port/departure.js'

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var Enum = sys.type.Enum;
    var Departure = ns.port.Departure;
    var ShipStatus = ns.port.ShipStatus;

    /**
     *  Departure Ship
     *  ~~~~~~~~~~~~
     *
     * @param {int|Enum} priority
     * @param {int|null} maxTries
     */
    var DepartureShip = function (priority, maxTries) {
        Object.call(this);
        if (priority === null) {
            priority = 0;
        } else if (Enum.isEnum(priority)) {
            priority = priority.valueOf();
        }
        if (maxTries === null) {
            maxTries = 1 + DepartureShip.RETRIES;
        }
        this.__priority = priority;  // task priority, smaller is faster
        this.__tries = maxTries;
        this.__expired = 0;          // timestamp in milliseconds
    };
    Class(DepartureShip, Object, [Departure], {

        // Override
        getPriority: function () {
            return this.__priority;
        },

        // Override
        touch: function (now) {
            // update retried time
            this.__expired = now + DepartureShip.EXPIRES;
            // decrease counter
            this.__tries -= 1;
        },

        // Override
        getStatus: function (now) {
            var fragments = this.getFragments();
            if (!fragments || fragments.length === 0) {
                return ShipStatus.DONE;
            } else if (this.__expired === 0) {
                return ShipStatus.NEW;
            //} else if (!this.isImportant()) {
            //    return ShipStatus.DONE;
            } else if (now < this.__expired) {
                return ShipStatus.WAITING;
            } else if (this.__tries > 0) {
                return ShipStatus.TIMEOUT;
            } else {
                return ShipStatus.FAILED;
            }
        }
    });

    /**
     *  Departure task will be expired after 2 minutes
     *  if no response received.
     */
    DepartureShip.EXPIRES = 120 * 1000;  // milliseconds

    /**
     *  Departure task will be retried 2 times
     *  if response timeout.
     */
    DepartureShip.RETRIES = 2;

    //-------- namespace --------
    ns.DepartureShip = DepartureShip;

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Class = sys.type.Class;
    var Arrays = sys.type.Arrays;
    var ShipStatus = ns.port.ShipStatus;

    /**
     *  Memory cache for Departures
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    var DepartureHall = function () {
        Object.call(this);
        // all departure ships
        this.__all_departures = [];  // Set<Departure>
        // new ships waiting to send out
        this.__new_departures = [];  // List<Departure>
        // ships waiting for responses
        this.__fleets = {};          // int(prior) => List<Departure>
        this.__priorities = [];      // List<int>
        // index
        this.__departure_map = {};   // SN => Departure
        this.__departure_level = {}; // SN => priority
        this.__finished_times = {};  // SN => timestamp
    }
    Class(DepartureHall, Object, null, null);

    /**
     *  Add outgoing ship to the waiting queue
     *
     * @param {Departure|Ship} outgo - departure task
     * @return {boolean} false on duplicated
     */
    DepartureHall.prototype.addDeparture = function (outgo) {
        // 1. check duplicated
        if (this.__all_departures.indexOf(outgo) >= 0) {
            return false;
        } else {
            this.__all_departures.push(outgo);
        }
        // 2. insert to the sorted queue
        var priority = outgo.getPriority();
        var index;
        for (index = 0; index < this.__new_departures.length; ++index) {
            if (this.__new_departures[index].getPriority() > priority) {
                // take the place before first ship
                // which priority is greater then this one.
                break;
            }
        }
        Arrays.insert(this.__new_departures, index, outgo);
        return true;
    };

    /**
     *  Check response from incoming ship
     *
     * @param {Arrival|Ship} response - incoming ship with SN
     * @return {Departure|Ship} finished task
     */
    DepartureHall.prototype.checkResponse = function (response) {
        var sn = response.getSN();
        // check whether this task has already finished
        var time = this.__finished_times[sn];
        if (time && time > 0) {
            return null;
        }
        // check departure
        var ship = this.__departure_map[sn];
        if (ship && ship.checkResponse(response)) {
            // all fragments sent, departure task finished
            // remove it and clear mapping when SN exists
            removeShip.call(this, ship, sn);
            // mark finished time
            this.__finished_times[sn] = (new Date()).getTime();
            return ship;
        }
        return null;
    };
    var removeShip = function (ship, sn) {
        var priority = this.__departure_level[sn];
        var fleet = this.__fleets[priority];
        if (fleet) {
            Arrays.remove(fleet, ship);
            // remove array when empty
            if (fleet.length === 0) {
                delete this.__fleets[priority];
            }
        }
        // remove mapping by SN
        delete this.__departure_map[sn];
        delete this.__departure_level[sn];
        Arrays.remove(this.__all_departures, ship);
    };

    /**
     *  Get next new/timeout task
     *
     * @param {number} now - current time
     * @return {Departure|Ship} departure task
     */
    DepartureHall.prototype.getNextDeparture = function (now) {
        // task.expired == 0
        var next = getNextNewDeparture.call(this, now);
        if (!next) {
            // task.expired < now
            next = getNextTimeoutDeparture.call(this, now);
        }
        return next;
    };
    var getNextNewDeparture = function (now) {
        if (this.__new_departures.length === 0) {
            return null;
        }
        // get first ship
        var outgo = this.__new_departures.shift();
        var sn = outgo.getSN();
        if (outgo.isImportant() && sn) {
            // this task needs response
            // choose an array with priority
            var priority = outgo.getPriority();
            insertShip.call(this, outgo, priority, sn);
            // build index for it
            this.__departure_map[sn] = outgo;
        } else {
            // disposable ship needs no response,
            // remove it immediately
            Arrays.remove(this.__all_departures, outgo);
        }
        // update expired time
        outgo.touch(now);
        return outgo;
    };
    var insertShip = function (outgo, priority, sn) {
        var fleet = this.__fleets[priority];
        if (!fleet) {
            // create new array for this priority
            fleet = [];
            this.__fleets[priority] = fleet;
            // insert the priority in a sorted list
            insertPriority.call(this, priority);
        }
        // append to the tail, and build index for it
        fleet.push(outgo);
        this.__departure_level[sn] = priority;
    };
    var insertPriority = function (priority) {
        var index, value;
        // seeking position for new priority
        for (index = 0; index < this.__priorities.length; ++index) {
            value = this.__priorities[index];
            if (value === priority) {
                // duplicated
                return;
            } else if (value > priority) {
                // got it
                break;
            }
            // current value is smaller than the new value,
            // keep going
        }
        // insert new value before the bigger one
        Arrays.insert(this.__priorities, index, priority);
    };
    var getNextTimeoutDeparture = function (now) {
        var priorityList = new Array(this.__priorities);
        var prior;
        var fleet, ship, sn, status;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            // 1. get tasks with priority
            prior = priorityList[i];
            fleet = this.__fleets[prior];
            if (!fleet) {
                continue;
            }
            // 2. seeking timeout task in this priority
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                sn = ship.getSN();
                status = ship.getStatus(now);
                if (status.equals(ShipStatus.TIMEOUT)) {
                    // response timeout, needs retry now.
                    // move to next priority
                    fleet.splice(j, 1);
                    insertShip.call(this, ship, prior + 1, sn);
                    // update expired time
                    ship.touch(now);
                    return ship;
                } else if (status.equals(ShipStatus.FAILED)) {
                    // try too many times and still missing response,
                    // task failed, remove this ship.
                    fleet.splice(j, 1);
                    // remove mapping by SN
                    delete this.__departure_map[sn];
                    delete this.__departure_level[sn];
                    Arrays.remove(this.__all_departures, ship);
                    return ship;
                }
            }
        }
        return null;
    };

    DepartureHall.prototype.purge = function () {
        var now = (new Date()).getTime();
        // 1. seeking finished tasks
        var prior;
        var fleet, ship, sn;
        var i, j;
        for (i = this.__priorities.length - 1; i >= 0; --i) {
            // get tasks with priority
            prior = this.__priorities[i];
            fleet = this.__fleets[prior];
            if (!fleet) {
                // this priority is empty
                this.__priorities.splice(i, 1);
                continue;
            }
            // seeking expired tasks in this priority
            for (j = fleet.length - 1; j >= 0; --j) {
                ship = fleet[j];
                if (ship.getStatus(now).equals(ShipStatus.DONE)) {
                    // task done
                    fleet.splice(j, 1);
                    sn = ship.getSN();
                    delete this.__departure_map[sn];
                    delete this.__departure_level[sn];
                    // mark finished time
                    this.__finished_times[sn] = now;
                }
            }
            // remove array when empty
            if (fleet.length === 0) {
                delete this.__fleets[prior];
                this.__priorities.splice(i, 1);
            }
        }
        // 3. seeking neglected finished times
        var ago = now - 3600 * 1000;
        var keys = Object.keys(this.__finished_times);
        var when;
        for (j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__finished_times[sn];
            if (!when || when < ago) {
                // long time ago
                delete this.__finished_times[sn];
                // // remove mapping with SN
                // delete this.__departure_map[sn];
            }
        }
    };

    //-------- namespace --------
    ns.DepartureHall = DepartureHall;

})(StarTrek, MONKEY);
