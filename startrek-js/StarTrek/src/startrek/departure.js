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

    var Departure = ns.port.Departure;

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
        } else if (priority instanceof sys.type.Enum) {
            priority = priority.valueOf();
        }
        if (maxTries === null) {
            maxTries = 1 + DepartureShip.RETRIES;
        }
        // task priority, smaller is faster
        this.__priority = priority;
        // tries:
        //    -1, this ship needs no response, so it will be sent out
        //        and removed immediately;
        //     0, this ship was sent and now is waiting for response,
        //        it should be removed after expired;
        //    >0, this ship needs retry and waiting for response,
        //        don't remove it now.
        this.__tries = maxTries;
        // expired time (timestamp in milliseconds)
        this.__expired = 0;
    };
    sys.Class(DepartureShip, Object, [Departure], null);

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

    // if (max_tries == -1),
    // means this ship will be sent only once
    // and no need to wait for response.
    DepartureShip.DISPOSABLE = -1;

    // Override
    DepartureShip.prototype.getPriority = function () {
        return this.__priority;
    };

    // Override
    DepartureShip.prototype.isNew = function () {
        return this.__expired === 0;
    };

    // Override
    DepartureShip.prototype.isDisposable = function () {
        return this.__tries <= 0;  // -1
    };

    // Override
    DepartureShip.prototype.isTimeout = function (now) {
        return this.__tries > 0 && now > this.__expired;
    };

    // Override
    DepartureShip.prototype.isFailed = function (now) {
        return this.__tries === 0 && now > this.__expired;
    };

    // Override
    DepartureShip.prototype.touch = function (now) {
        // update retried time
        this.__expired = now + DepartureShip.EXPIRES;
        // decrease counter
        this.__tries -= 1;
    };

    //-------- namespace --------
    ns.DepartureShip = DepartureShip;

    ns.registers('DepartureShip');

})(StarTrek, MONKEY);

(function (ns, sys) {
    'use strict';

    var Arrays = ns.type.Arrays;
    var Dictionary = sys.type.Dictionary;

    var DepartureHall = function () {
        Object.call(this);
        this.__priorities = [];           // int[]
        this.__fleets = new Dictionary(); // int(prior) => Departure[]
        this.__dmap = new Dictionary();   // ID => Arrival
        this.__dft = new Dictionary();    // ID => timestamp
    }
    sys.Class(DepartureHall, Object, null, null);

    /**
     *  Append outgoing ship to a fleet with priority
     *
     * @param {Departure|Ship} outgo - departure task
     * @return {boolean} false on duplicated
     */
    DepartureHall.prototype.appendDeparture = function (outgo) {
        var priority = outgo.getPriority();
        // 1. choose an array with priority
        var fleet = this.__fleets.getValue(priority);
        if (!fleet) {
            // 1.1. create new array for this priority
            fleet = [];
            this.__fleets.setValue(priority, fleet);
            // 1.2. insert the priority in  a sorted list
            insertPriority(priority, this.__priorities);
        } else {
            // 1.3. check duplicated task
            if (fleet.indexOf(outgo) >= 0) {
                return false;
            }
        }
        // 2. append to the tail
        fleet.push(outgo);
        // 3. build mapping if SN exists
        var sn = outgo.getSN();
        if (sn && !outgo.isDisposable()) {
            // disposable ship needs no response, so
            // we don't build index for it
            this.__dmap.setValue(sn, outgo);
        }
        return true;
    };
    var insertPriority = function (prior, priorities) {
        var index, value;
        // seeking position for new priority
        for (index = 0; index < priorities.length; ++index) {
            value = priorities[index];
            if (value === prior) {
                // duplicated
                return;
            } else if (value > prior) {
                // got it
                break;
            }
            // current value is smaller than the new value,
            // keep going
        }
        // insert new value before the bigger one
        Arrays.insert(priorities, index, prior);
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
        var time = this.__dft.getValue(sn);
        if (!time || time === 0) {
            // check departure
            var ship = this.__dmap.getValue(sn);
            if (ship && ship.checkResponse(response)) {
                // all fragments sent, departure task finished
                // remove it and clear mapping when SN exists
                removeShip(ship, sn, this.__fleets, this.__dmap);
                // mark finished time
                this.__dft.setValue(sn, (new Date()).getTime());
                return ship;
            }
        }
        return null;
    };
    var removeShip = function (ship, sn, departureFleets, departureMap) {
        var prior = ship.getPriority();
        var fleet = departureFleets.getValue(prior);
        if (fleet) {
            Arrays.remove(fleet, ship);
            // remove array when empty
            if (fleet.length === 0) {
                departureFleets.removeValue(prior);
            }
        }
        // remove mapping by SN
        departureMap.removeValue(sn);
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
            // task.tries > 0 and timeout
            next = getNextTimeoutDeparture.call(this, now);
        }
        return next;
    };
    var getNextNewDeparture = function (now) {
        var priorityList = new Array(this.__priorities);
        var prior, sn;
        var fleet, ship;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            // 1. get tasks with priority
            prior = priorityList[i];
            fleet = this.__fleets.getValue(prior);
            if (!fleet) {
                continue;
            }
            // 2. seeking new task in this priority
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                if (ship.isNew()) {
                    if (ship.isDisposable()) {
                        // disposable ship needs no response,
                        // remove it immediately.
                        fleet.splice(j, 1); //fleet.remove(ship);
                        // TODO: disposable ship will not be mapped.
                        //       see 'appendDeparture()'
                        sn = ship.getSN();
                        if (sn) {
                            this.__dmap.removeValue(sn);
                        }
                    } else {
                        // first try, update expired time for response
                        ship.touch(now);
                    }
                    return ship;
                }
            }
        }
        return null;
    };
    var getNextTimeoutDeparture = function (now) {
        var priorityList = new Array(this.__priorities);
        var prior, sn;
        var fleet, ship;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            // 1. get tasks with priority
            prior = priorityList[i];
            fleet = this.__fleets.getValue(prior);
            if (!fleet) {
                continue;
            }
            // 2. seeking timeout task in this priority
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                if (ship.isTimeout(now)) {
                    // response timeout, needs retry now.
                    // 2.1. update expired time;
                    ship.touch(now);
                    // 2.2. move to the tail
                    if (fleet.length > 1/* && fleet.length > (j + 1)*/) {
                        fleet.splice(j, 1);
                        fleet.push(ship);
                    }
                    return ship;
                } else if (ship.isFailed(now)) {
                    // try too many times and still missing response,
                    // task failed, remove this ship.
                    fleet.splice(j, 1);
                    sn = ship.getSN();
                    if (sn) {
                        this.__dmap.removeValue(sn);
                    }
                    return ship;
                }
            }
        }
        return null;
    };

    DepartureHall.prototype.purge = function () {
        var failedTasks = [];
        var now = (new Date()).getTime();
        var priorityList = new Array(this.__priorities);
        var prior;
        var fleet, ship;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            // 0. get tasks with priority
            prior = priorityList[i];
            fleet = this.__fleets.getValue(prior);
            if (!fleet) {
                continue;
            }
            // 1. seeking expired tasks in this priority
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                if (ship.isFailed(now)) {
                    // task expired
                    failedTasks.push(ship);
                }
            }
            // 2. clear expired tasks
            clear.call(this, fleet, failedTasks, prior);
            failedTasks = [];
        }
        // 3. seeking neglected finished times
        var ago = now - 3600;
        var keys = this.__dft.allKeys();
        var sn, when;
        for (j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__dft.getValue(sn);
            if (!when || when < ago) {
                // long time ago
                this.__dft.removeValue(sn);
                // remove mapping with SN
                this.__dmap.removeValue(sn);
            }
        }
    };
    var clear = function (fleet, failedTasks, prior) {
        var sn, ship;
        for (var index = failedTasks.length - 1; index >= 0; --index) {
            ship = fleet[index];
            fleet.splice(index, 1);
            // remove mapping when SN exists
            sn = ship.getSN();
            if (sn) {
                this.__dmap.removeValue(sn);
            }
            // TODO: callback?
        }
        // remove array when empty
        if (fleet.length === 0)  {
            this.__fleets.removeValue(prior);
        }
    };

    //-------- namespace --------
    ns.DepartureHall = DepartureHall;

    ns.registers('DepartureHall');

})(StarTrek, MONKEY);
