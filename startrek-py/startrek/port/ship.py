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
from typing import List, Optional

from ..types import Address
from ..net import Connection


class Ship(ABC):

    @property
    def sn(self):
        """ Get ID for this ship """
        raise NotImplemented

    @abstractmethod
    def is_failed(self, now: int) -> bool:
        """
        Check whether task failed

        :param now: current timestamp
        :return true on failed
        """
        raise NotImplemented

    @abstractmethod
    def update(self, now: int) -> bool:
        """
        Update expired time

        :param now: current timestamp
        :return false on error (nothing changed)
        """
        raise NotImplemented


class Arrival(Ship):
    """ Incoming Ship """

    @abstractmethod
    def assemble(self, ship):  # -> Optional[Arrival]:
        """
        Data package can be sent as separated batches

        :param ship: arrival ship carrying with data package/fragment
        :return new ship carrying the whole data package
        """
        raise NotImplemented


class Departure(Ship):
    """ Outgoing Ship """

    @property
    def priority(self) -> int:
        raise NotImplemented

    @property
    def retries(self) -> int:
        """ How many times retried """
        raise NotImplemented

    @abstractmethod
    def is_timeout(self, now: int) -> bool:
        """
        Check whether task needs retry

        :param now: current time
        :return true on retry
        """
        raise NotImplemented

    @property
    def fragments(self) -> List[bytes]:
        """
        Get fragments to sent

        :return remaining (separated) data package
        """
        raise NotImplemented

    @abstractmethod
    def check_response(self, ship: Arrival) -> bool:
        """
        The received ship may carried a response for the departure
        if all fragments responded, means this task is finished.

        :param ship: income ship carrying response
        :return true on task finished
        """
        raise NotImplemented


class Priority(IntEnum):
    """ Departure Ship Priority """

    URGENT = -1
    NORMAL = 0
    SLOWER = 1


class ShipDelegate(ABC):
    """ Ship Delegate """

    @abstractmethod
    def gate_received(self, ship: Arrival,
                      source: Address, destination: Optional[Address], connection: Connection):
        """
        Callback when new package received

        :param ship:        income data package container
        :param source:      remote address
        :param destination: local address
        :param connection:  current connection
        """
        raise NotImplemented

    @abstractmethod
    def gate_sent(self, ship: Departure,
                  source: Optional[Address], destination: Address, connection: Connection):
        """
        Callback when package sent

        :param ship:        outgo data package container
        :param source:      local address
        :param destination: remote address
        :param connection:  current connection
        """
        raise NotImplemented

    @abstractmethod
    def gate_error(self, error: IOError, ship: Departure,
                   source: Optional[Address], destination: Address, connection: Connection):
        """
        Callback when package sent

        :param error:       error message
        :param ship:        outgo data package container
        :param source:      local address
        :param destination: remote address
        :param connection:  current connection
        """
        raise NotImplemented
