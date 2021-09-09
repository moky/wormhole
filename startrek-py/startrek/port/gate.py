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

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Optional

from ..fsm import Processor
from ..net import ConnectionState

from .ship import Arrival, Departure


class Status(IntEnum):
    """ Gate Status """
    ERROR = -1
    INIT = 0
    PREPARING = 1
    READY = 2


def status_from_state(state: ConnectionState) -> Status:
    if state is None:
        return Status.INIT
    if state in [ConnectionState.READY, ConnectionState.EXPIRED, ConnectionState.MAINTAINING]:
        return Status.READY
    if state == ConnectionState.PREPARING:
        return Status.PREPARING
    if state == ConnectionState.ERROR:
        return Status.ERROR
    return Status.INIT


class Gate(Processor):
    """
        Star Gate
        ~~~~~~~~~~~
    """

    @abstractmethod
    def send_data(self, data: bytes, source: Optional[tuple], destination: tuple) -> bool:
        """
        Send data to the remote peer

        :param data:        outgoing data package
        :param source:      local address
        :param destination: remote address
        :return False on error
        """
        raise NotImplemented

    @abstractmethod
    def gate_status(self, remote: tuple, local: Optional[tuple]) -> Status:
        """
        Get gate status with direction

        :param remote: remote address
        :param local:  local address
        :return gate status
        """
        raise NotImplemented


class Delegate(ABC):

    @abstractmethod
    def gate_status_changed(self, gate: Gate, remote: tuple, local: Optional[tuple],
                            previous: Status, current: Status):
        """
        Callback when connection status changed

        :param gate:     current gate
        :param remote:   remote address
        :param local:    local address
        :param previous: old status
        :param current:  new status
        """
        raise NotImplemented

    @abstractmethod
    def gate_received(self, gate: Gate, source: tuple, destination: Optional[tuple], ship: Arrival):
        """
        Callback when new package received

        :param gate:        current gate
        :param source:      remote address
        :param destination: local address
        :param ship:        data package container
        """
        raise NotImplemented

    @abstractmethod
    def gate_sent(self, gate: Gate, source: Optional[tuple], destination: tuple, ship: Departure):
        """
        Callback when package sent

        :param gate:        current gate
        :param source:      local address
        :param destination: remote address
        :param ship:        data package container
        """
        raise NotImplemented

    @abstractmethod
    def gate_error(self, gate: Gate, source: Optional[tuple], destination: tuple, ship: Departure, error):
        """
        Callback when package sent

        :param gate:        current gate
        :param source:      local address
        :param destination: remote address
        :param ship:        data package container
        :param error:       error message
        """
        raise NotImplemented
