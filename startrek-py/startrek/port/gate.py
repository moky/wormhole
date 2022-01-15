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

from ..types import Address
from ..fsm import Processor
from ..net import Connection, ConnectionState

from .ship import ShipDelegate


class Status(IntEnum):
    """ Gate Status """
    ERROR = -1
    INIT = 0
    PREPARING = 1
    READY = 2


def status_from_state(state: ConnectionState) -> Status:
    if state is None:
        return Status.ERROR
    if state in [ConnectionState.READY, ConnectionState.EXPIRED, ConnectionState.MAINTAINING]:
        return Status.READY
    if state == ConnectionState.PREPARING:
        return Status.PREPARING
    if state == ConnectionState.ERROR:
        return Status.ERROR
    return Status.INIT


class GateDelegate(ShipDelegate, ABC):

    @abstractmethod
    def gate_status_changed(self, previous: Status, current: Status, remote: Address, local: Optional[Address], gate):
        """
        Callback when connection status changed

        :param previous: old status
        :param current:  new status
        :param remote:   remote address
        :param local:    local address
        :param gate:     current gate
        """
        raise NotImplemented


class Gate(Processor):
    """
        Star Gate
        ~~~~~~~~~
    """

    @abstractmethod
    def get_connection(self, remote: Address, local: Optional[Address]) -> Optional[Connection]:
        """
        Get connection with direction

        :param remote: remote address
        :param local:  local address
        :return: None on failed
        """
        raise NotImplemented

    @abstractmethod
    def gate_status(self, remote: Address, local: Optional[Address]) -> Status:
        """
        Get gate status with direction

        :param remote: remote address
        :param local:  local address
        :return gate status
        """
        raise NotImplemented

    @property
    def delegate(self) -> Optional[GateDelegate]:
        """ Get delegate for handling events """
        raise NotImplemented
