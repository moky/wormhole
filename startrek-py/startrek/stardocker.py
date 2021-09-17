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

import socket
import time
from abc import abstractmethod
from typing import Optional

from .net import Connection
from .port import Arrival, Departure, ShipDelegate
from .port import Docker

from .dock import Dock, LockedDock


class StarDocker(Docker):
    """
        Star Docker
        ~~~~~~~~~~~

        @abstract properties:
            connection()
            delegate()

        @abstract methods:
            - get_arrival(data)
            - check_arrival(ship)
            - pack(payload, priority)
            - heartbeat()
    """

    def __init__(self, remote: tuple, local: Optional[tuple]):
        super().__init__()
        self.__remote = remote
        self.__local = local
        self.__dock = self._create_dock()

    # noinspection PyMethodMayBeStatic
    def _create_dock(self) -> Dock:
        """ Override for user-customized dock """
        return LockedDock()

    @property
    def remote_address(self) -> tuple:
        return self.__remote

    @property
    def local_address(self) -> Optional[tuple]:
        return self.__local

    @property
    def connection(self) -> Optional[Connection]:
        """ Get related connection with status is 'ready' """
        raise NotImplemented

    @property
    def delegate(self) -> ShipDelegate:
        """ Get delegate for handling events """
        raise NotImplemented

    # Override
    def process(self) -> bool:
        # 1. get connection with is ready for sending data
        conn = self.connection
        if conn is None:
            # connection not ready now
            return False
        now = int(time.time())
        # 2. get outgo task
        outgo = self.next_departure(now=now)
        if outgo is None:
            # nothing to do now
            return False
        # 3. process outgo task
        error = None
        if outgo.is_failed(now=now):
            # outgo ship expired, callback
            error = ConnectionError('Request timeout')
        else:
            try:
                if not self.__send_departure(ship=outgo):
                    # failed to send outgo package, callback
                    error = ConnectionError('Connection error')
            except socket.error as e:
                # socket error, callback
                error = e
        # callback
        delegate = self.delegate
        if error is not None and delegate is not None:
            remote = self.__remote
            local = self.__local
            delegate.gate_error(error=error, ship=outgo, source=local, destination=remote, connection=conn)
        return True

    def __send_departure(self, ship: Departure) -> bool:
        """ Sending all fragments in the ship """
        fragments = ship.fragments
        if fragments is None or len(fragments) == 0:
            # all fragments sent
            return True
        conn = self.connection
        if conn is None:
            # connection not ready now
            return False
        remote = self.__remote
        success = 0
        for pkg in fragments:
            if conn.send(data=pkg, target=remote) != -1:
                success += 1
        return success == len(fragments)

    # Override
    def process_received(self, data: bytes):
        # 1. get income ship from received data
        income = self.get_arrival(data=data)
        if income is None:
            return None
        # 2. check income ship for response
        income = self.check_arrival(ship=income)
        if income is None:
            return None
        # 3. process income ship with completed data package
        delegate = self.delegate
        if delegate is None:
            return None
        # callback
        remote = self.__remote
        local = self.__local
        conn = self.connection
        delegate.gate_received(ship=income, source=remote, destination=local, connection=conn)

    @abstractmethod
    def get_arrival(self, data: bytes) -> Optional[Arrival]:
        """
        Get income ship from received data

        :param data: received data
        :return income ship carrying data package/fragment
        """
        raise NotImplemented

    @abstractmethod
    def check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """
        Check income ship for responding

        :param ship: income ship carrying data package/fragment/response
        :return income ship carrying completed data package
        """
        raise NotImplemented

    # protected
    def check_response(self, ship: Arrival) -> Optional[Departure]:
        """ Check and remove linked departure ship with same SN (and page index for fragment) """
        # check response for linked departure ship (same SN)
        linked = self.__dock.check_response(ship=ship)
        if linked is None:
            # linked departure task not found, or not finished yet
            return None
        # all fragments responded, task finished
        delegate = self.delegate
        if delegate is not None:
            remote = self.__remote
            local = self.__local
            conn = self.connection
            delegate.gate_sent(ship=linked, source=local, destination=remote, connection=conn)
        return linked

    # protected
    def assemble_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """ Check received ship for completed package """
        return self.__dock.assemble_arrival(ship=ship)

    # protected
    def next_departure(self, now: int) -> Optional[Departure]:
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
