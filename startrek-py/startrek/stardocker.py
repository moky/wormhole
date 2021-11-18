# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import time
import weakref
from abc import abstractmethod
from typing import Optional

from .types import AddressPairObject
from .net import Connection, Hub
from .port import Arrival, Departure
from .port import Docker, Gate, GateDelegate

from .dock import Dock, LockedDock


class StarDocker(AddressPairObject, Docker):
    """
        Star Docker
        ~~~~~~~~~~~

        @abstract properties:
            connection()
            delegate()

        @abstract methods:
            - pack(payload, priority)
            - heartbeat()
            - _get_arrival(data)
            - _check_arrival(ship)
    """

    def __init__(self, remote: tuple, local: Optional[tuple], gate: Gate):
        super().__init__(remote=remote, local=local)
        self.__gate = weakref.ref(gate)
        self.__dock = self._create_dock()

    # noinspection PyMethodMayBeStatic
    def _create_dock(self) -> Dock:
        """ Override for user-customized dock """
        return LockedDock()

    @property  # protected
    def gate(self) -> Gate:
        return self.__gate()

    @property  # protected
    def hub(self) -> Optional[Hub]:
        raise NotImplemented

    @property  # Override
    def remote_address(self) -> tuple:  # (str, int)
        return self._remote

    @property  # Override
    def local_address(self) -> Optional[tuple]:  # (str, int)
        return self._local

    @property  # Override
    def connection(self) -> Optional[Connection]:
        gate = self.gate
        if gate is not None:
            return gate.get_connection(remote=self._remote, local=self._local)

    @property  # Override
    def delegate(self) -> Optional[GateDelegate]:
        gate = self.gate
        if gate is not None:
            return gate.delegate

    # Override
    def process(self) -> bool:
        # 1. get connection which is ready for sending data
        conn = self.connection
        if conn is None or not conn.alive:
            # connection not ready now
            return False
        now = int(time.time())
        # 2. get outgo task
        outgo = self._next_departure(now=now)
        if outgo is None:
            # nothing to do now
            return False
        # 3. process outgo task
        try:
            error = self.__send_departure(ship=outgo, now=now)
            if error is None:
                # task done
                return True
        except Exception as e:
            # socket error, callback
            error = e
        # callback for error
        delegate = self.delegate
        if delegate is not None:
            remote = self.remote_address
            local = self.local_address
            delegate.gate_error(error=error, ship=outgo, source=local, destination=remote, connection=conn)
        # return False here will cause thread idling
        # if this task is failed, return True to process next one
        return isinstance(error, TimeoutError)

    def __send_departure(self, ship: Departure, now: int) -> Optional[OSError]:
        """ Sending all fragments in the ship """
        # check task
        if ship.is_failed(now=now):
            return TimeoutError('Request timeout')
        fragments = ship.fragments
        if fragments is None or len(fragments) == 0:
            # all fragments have been sent already
            return None
        # check connection
        conn = self.connection
        assert conn is not None and conn.alive, 'connection not ready now'
        remote = self.remote_address
        # send all fragments
        total = len(fragments)
        success = 0
        for pkg in fragments:
            if conn.send(data=pkg, target=remote) != -1:
                success += 1
        if success == total:
            # all fragments sent successfully
            return None
        else:
            return ConnectionError('only %d/%d fragments sent' % (success, total))

    # Override
    def process_received(self, data: bytes):
        # 1. get income ship from received data
        income = self._get_arrival(data=data)
        if income is None:
            return None
        # 2. check income ship for response
        income = self._check_arrival(ship=income)
        if income is None:
            return None
        # 3. callback for processing income ship with completed data package
        delegate = self.delegate
        if delegate is not None:
            remote = self.remote_address
            local = self.local_address
            conn = self.connection
            delegate.gate_received(ship=income, source=remote, destination=local, connection=conn)

    @abstractmethod
    def _get_arrival(self, data: bytes) -> Optional[Arrival]:
        """
        Get income ship from received data

        :param data: received data
        :return income ship carrying data package/fragment
        """
        raise NotImplemented

    @abstractmethod
    def _check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """
        Check income ship for responding

        :param ship: income ship carrying data package/fragment/response
        :return income ship carrying completed data package
        """
        raise NotImplemented

    # protected
    def _check_response(self, ship: Arrival) -> Optional[Departure]:
        """ Check and remove linked departure ship with same SN (and page index for fragment) """
        # check response for linked departure ship (same SN)
        linked = self.__dock.check_response(ship=ship)
        if linked is None:
            # linked departure task not found, or not finished yet
            return None
        # all fragments responded, task finished
        delegate = self.delegate
        if delegate is not None:
            remote = self.remote_address
            local = self.local_address
            conn = self.connection
            delegate.gate_sent(ship=linked, source=local, destination=remote, connection=conn)
        return linked

    # protected
    def _assemble_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """ Check received ship for completed package """
        return self.__dock.assemble_arrival(ship=ship)

    # protected
    def _next_departure(self, now: int) -> Optional[Departure]:
        """ Get outgo ship from waiting queue """
        # this will be remove from the queue,
        # if needs retry, the caller should append it back
        return self.__dock.next_departure(now=now)

    # Override
    def append_departure(self, ship: Departure) -> bool:
        """ Append outgo Ship to the waiting queue """
        return self.__dock.append_departure(ship=ship)

    # Override
    def purge(self):
        """ Clear expired tasks """
        self.__dock.purge()

    # Override
    def close(self):
        hub = self.hub
        if hub is not None:
            remote = self.remote_address
            local = self.local_address
            hub.disconnect(remote=remote, local=local)
