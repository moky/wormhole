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

//! require 'port/departure.js'

    /**
     *  Departure Ship
     *  ~~~~~~~~~~~~
     *
     * @param {int|null} priority
     * @param {uint|null} maxTries
     */
    st.DepartureShip = function (priority, maxTries) {
        BaseObject.call(this);
        if (priority === null) {
            priority = DeparturePriority.NORMAL;
        }
        if (maxTries === null) {
            maxTries = 1 + DepartureShip.RETRIES;
        }
        this.__priority = priority;  // task priority, smaller is faster
        this.__tries = maxTries;
        this.__expired = null;       // Date
    };
    var DepartureShip = st.DepartureShip;

    Class(DepartureShip, BaseObject, [Departure]);

    /**
     *  Departure task will be expired after 2 minutes
     *  if no response received.
     */
    DepartureShip.EXPIRES = Duration.ofMinutes(2);

    /**
     *  Departure task will be retried 2 times
     *  if response timeout.
     */
    DepartureShip.RETRIES = 2;

    // Override
    DepartureShip.prototype.getPriority = function () {
        return this.__priority;
    };

    // Override
    DepartureShip.prototype.touch = function (now) {
        // update retried time
        this.__expired = DepartureShip.EXPIRES.addTo(now);
        // decrease counter
        this.__tries -= 1;
    };

    // Override
    DepartureShip.prototype.getStatus = function (now) {
        var expired = this.__expired;
        var fragments = this.getFragments();
        if (!fragments || fragments.length === 0) {
            return ShipStatus.DONE;
        } else if (!expired) {
            return ShipStatus.NEW;
        //} else if (!this.isImportant()) {
        //    return ShipStatus.DONE;
        } else if (now.getTime() < expired.getTime()) {
            return ShipStatus.WAITING;
        } else if (this.__tries > 0) {
            return ShipStatus.TIMEOUT;
        } else {
            return ShipStatus.FAILED;
        }
    };


    /**
     *  Memory cache for Departures
     *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
     */
    st.DepartureHall = function () {
        BaseObject.call(this);
        // all departure ships
        this.__all_departures = new HashSet();  // WeakSet<Departure>
        // new ships waiting to send out
        this.__new_departures = [];             // List<Departure>
        // ships waiting for responses
        this.__fleets = {};                     // int(prior) => List<Departure>
        this.__priorities = [];                 // List<int>
        // index
        this.__departure_map = {};              // SN => Departure
        this.__departure_level = {};            // SN => priority
        this.__finished_times = {};             // SN => Date
    };
    var DepartureHall = st.DepartureHall;

    Class(DepartureHall, BaseObject, null);

    /**
     *  Add outgoing ship to the waiting queue
     *
     * @param {st.port.Departure} outgo - departure task
     * @return {boolean} false on duplicated
     */
    DepartureHall.prototype.addDeparture = function (outgo) {
        // 1. check duplicated
        if (this.__all_departures.contains(outgo)) {
            return false;
        } else {
            this.__all_departures.add(outgo);
        }
        // 2. insert to the sorted queue
        var priority = outgo.getPriority();
        var index = this.__new_departures.length;
        while (index > 0) {
            --index;
            if (this.__new_departures[index].getPriority() <= priority) {
                // take the place before first ship
                // which priority is greater then this one.
                ++index;  // insert after
                break;
            }
        }
        Arrays.insert(this.__new_departures, index, outgo);
        return true;
    };

    /**
     *  Check response from incoming ship
     *
     * @param {Arrival|st.port.Ship} response - incoming ship with SN
     * @return {Departure|Ship} finished task
     */
    DepartureHall.prototype.checkResponse = function (response) {
        var sn = response.getSN();
        // check whether this task has already finished
        var time = this.__finished_times[sn];
        if (time) {
            return null;
        }
        // check departure
        var ship = this.__departure_map[sn];
        if (ship && ship.checkResponse(response)) {
            // all fragments sent, departure task finished
            // remove it and clear mapping when SN exists
            removeDeparture.call(this, ship, sn);
            // mark finished time
            this.__finished_times[sn] = new Date();
            return ship;
        }
        return null;
    };
    var removeDeparture = function (ship, sn) {
        var priority = this.__departure_level[sn];
        if (!priority) {
            priority = 0;
        }
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
        this.__all_departures.remove(ship);
    };

    /**
     *  Get next new/timeout task
     *
     * @param {Date} now - current time
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
            insertDeparture.call(this, outgo, priority, sn);
            // build index for it
            this.__departure_map[sn] = outgo;
        } else {
            // disposable ship needs no response,
            // remove it immediately
            this.__all_departures.remove(outgo);
        }
        // update expired time
        outgo.touch(now);
        return outgo;
    };
    var insertDeparture = function (outgo, priority, sn) {
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
        var priorityList = this.__priorities.slice();  // copy
        var departures;  // List<Departure>
        var fleet;       // List<Departure>
        var ship;        // Departure
        var status;      // ShipStatus;
        var sn;
        var prior;       // int
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            prior = priorityList[i];
            // 1. get tasks with priority
            fleet = this.__fleets[prior];
            if (!fleet) {
                continue;
            }
            // 2. seeking timeout task in this priority
            departures = fleet.slice();
            for (j = 0; j < departures.length; ++j) {
                ship = departures[j];
                sn = ship.getSN();
                status = ship.getStatus(now);
                if (status === ShipStatus.TIMEOUT) {
                    // response timeout, needs retry now.
                    // move to next priority
                    fleet.splice(j, 1);
                    insertDeparture.call(this, ship, prior + 1, sn);
                    // update expired time
                    ship.touch(now);
                    return ship;
                } else if (status === ShipStatus.FAILED) {
                    // try too many times and still missing response,
                    // task failed, remove this ship.
                    fleet.splice(j, 1);
                    // remove mapping by SN
                    delete this.__departure_map[sn];
                    delete this.__departure_level[sn];
                    this.__all_departures.remove(ship);
                    return ship;
                }
            }
        }
        return null;
    };

    DepartureHall.prototype.purge = function (now) {
        if (!now) {
            now = new Date();
        }
        var count = 0;
        // 1. seeking finished tasks
        var priorityList = this.__priorities.slice();  // copy
        var departures;  // List<Departure>
        var fleet;       // List<Departure>
        var ship;        // Departure
        var sn;
        var prior;       // int
        var i, j;
        for (i = priorityList.length - 1; i >= 0; --i) {
            prior = priorityList[i];
            // get tasks with priority
            fleet = this.__fleets[prior];
            if (!fleet) {
                // this priority is empty
                this.__priorities.splice(i, 1);
                continue;
            }
            // seeking expired tasks in this priority
            departures = fleet.slice();  // copy
            for (j = departures.length - 1; j >= 0; --j) {
                ship = departures[j];
                if (ship.getStatus(now) === ShipStatus.DONE) {
                    // task done
                    fleet.splice(j, 1);
                    sn = ship.getSN();
                    delete this.__departure_map[sn];
                    delete this.__departure_level[sn];
                    // mark finished time
                    this.__finished_times[sn] = now;
                    ++count;
                }
            }
            // remove array when empty
            if (fleet.length === 0) {
                delete this.__fleets[prior];
                this.__priorities.splice(i, 1);
            }
        }
        // 3. seeking neglected finished times
        var finished_times = this.__finished_times;
        var ago = Duration.ofMinutes(60).subtractFrom(now);
        ago = ago.getTime();
        Mapper.forEach(finished_times, function (sn, when) {
            if (!when || when.getTime() < ago) {
                // long time ago
                delete finished_times[sn];
                // // remove mapping with SN
                // delete this.__departure_map[sn];
            }
            return false;
        });
        return count;
    };
