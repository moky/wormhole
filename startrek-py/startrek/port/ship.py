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
from typing import Any, List

"""
    Star Ship
    ~~~~~~~~~
    
    Container carrying data package
"""


class DeparturePriority(IntEnum):
    """ Departure Ship Priority """

    URGENT = -1
    NORMAL = 0
    SLOWER = 1


class ShipStatus(IntEnum):
    """ Ship Status """
    #
    #  Departure Status
    #
    NEW = 0x00      # not try yet
    WAITING = 0x01  # sent, waiting for responses
    TIMEOUT = 0x02  # waiting to send again
    DONE = 0x03     # all fragments responded (or no need respond)
    FAILED = 0x04   # tried 3 times and missed response(s)
    #
    #  Arrival Status
    #
    ASSEMBLING = 0x10  # waiting for more fragments
    EXPIRED = 0x11     # failed to received all fragments


class Ship(ABC):

    @property
    @abstractmethod
    def sn(self) -> Any:
        """
        Get ID for this ship

        :return: SN
        """
        raise NotImplemented

    @abstractmethod
    def touch(self, now: float):
        """
        Update expired time

        :param now: current time
        """
        raise NotImplemented

    @abstractmethod
    def get_status(self, now: float) -> ShipStatus:
        """
        Check ship state

        :param now: current time
        :return: current status
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
    @abstractmethod
    def priority(self) -> int:
        """ Task priority, default is 0, smaller is faster """
        raise NotImplemented

    @property
    @abstractmethod
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
        :return True on task finished
        """
        raise NotImplemented

    #
    #   task states
    #

    @property
    @abstractmethod
    def is_important(self) -> bool:
        """
        Whether needs to wait for responses

        :return false for disposable
        """
        raise NotImplemented
