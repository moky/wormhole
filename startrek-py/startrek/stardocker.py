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

from .port import Arrival, Departure
from .port import Docker, Gate, GateStatus, GateDelegate

from .dock import Dock, LockedDock


class StarDocker(Docker):
    """
        Star Docker
        ~~~~~~~~~~~

        @abstract properties:
            gate()
            delegate()

        @abstract methods:
            - get_income_ship(data)
            - check_income_ship(ship)
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
        return LockedDock()

    @property
    def remote_address(self) -> tuple:
        return self.__remote

    @property
    def local_address(self) -> Optional[tuple]:
        return self.__local

    @property
    def gate(self) -> Gate:
        raise NotImplemented

    @property
    def delegate(self) -> GateDelegate:
        raise NotImplemented

    @property
    def __is_ready(self) -> bool:
        status = self.gate.gate_status(remote=self.__remote, local=self.__local)
        return status == GateStatus.READY

    # Override
    def process(self) -> bool:
        # 1. check gate status
        if not self.__is_ready:
            # not ready yet
            return False
        now = int(time.time())
        # 2. get outgo task
        outgo = self.get_outgo_ship(now=now)
        if outgo is None:
            # nothing to do now
            return False
        # 3. process outgo
        if outgo.is_failed(now=now):
            # outgo ship expired, callback
            self.__outgo_error(msg='Request timeout', ship=outgo)
        else:
            try:
                if not self.send_outgo_ship(ship=outgo):
                    # failed to send outgo package, callback
                    self.__outgo_error(msg='Connection error', ship=outgo)
            except socket.error as error:
                self.__outgo_error(msg=str(error), ship=outgo)
        return True

    def __outgo_error(self, msg: str, ship: Departure):
        delegate = self.delegate
        if delegate is not None:
            local = self.__local
            remote = self.__remote
            error = ConnectionError(msg)
            delegate.gate_error(gate=self.gate, source=local, destination=remote, ship=ship, error=error)

    # Override
    def process_received(self, data: bytes):
        # 1. get income ship from received data
        income = self.get_income_ship(data=data)
        if income is not None:
            # 2. check income ship for response
            income = self.check_income_ship(ship=income)
            if income is not None:
                # 3. process income ship with completed data package
                self.process_income_ship(ship=income)

    @abstractmethod
    def get_income_ship(self, data: bytes) -> Optional[Arrival]:
        """
        Get income ship from received data

        :param data: received data
        :return income ship carrying data package/fragment
        """
        raise NotImplemented

    @abstractmethod
    def check_income_ship(self, ship: Arrival) -> Optional[Arrival]:
        """
        Check income ship for responding

        :param ship: income ship carrying data package/fragment/response
        :return income ship carrying completed data package
        """
        raise NotImplemented

    # protected
    def check_response(self, ship: Arrival):
        # check response for linked departure ship (same SN)
        linked = self.__dock.check_response(ship=ship)
        if linked is not None:
            # all fragments responded, task finished
            delegate = self.delegate
            if delegate is not None:
                local = self.__local
                remote = self.__remote
                delegate.gate_sent(gate=self.gate, source=local, destination=remote, ship=linked)

    # protected
    def process_income_ship(self, ship: Arrival):
        local = self.__local
        remote = self.__remote
        delegate = self.delegate
        assert delegate is not None, 'gate delegate should not empty'
        delegate.gate_received(gate=self.gate, source=remote, destination=local, ship=ship)

    # protected
    def get_outgo_ship(self, now: int) -> Optional[Departure]:
        """
        Get outgo ship from waiting queue

        :param now: current timestamp
        :return next new/timeout task
        """
        # this will be remove from the queue,
        # if needs retry, the caller should append it back
        return self.__dock.next_departure(now=now)

    # protected
    def send_outgo_ship(self, ship: Departure) -> bool:
        fragments = ship.fragments
        if fragments is None or len(fragments) == 0:
            return True
        gate = self.gate
        local = self.__local
        remote = self.__remote
        success = 0
        for pack in fragments:
            if gate.send_data(data=pack, source=local, destination=remote):
                success += 1
        return success == len(fragments)
