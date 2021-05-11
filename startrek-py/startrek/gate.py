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

from .ship import Ship, ShipDelegate
from .starship import StarShip


"""
    Star Gate
    ~~~~~~~~~
    
    Connected remote peer
"""


class GateStatus(IntEnum):
    """ Star Gate Status """

    Error = -1
    Init = 0
    Connecting = 1
    Connected = 2


class GateDelegate(ABC):
    """ Star Gate Delegate """

    @abstractmethod
    def gate_status_changed(self, gate, old_status: GateStatus, new_status: GateStatus):
        """
        Callback when connection status changed

        :param gate:       remote gate
        :param old_status: last status
        :param new_status: current status
        """
        raise NotImplemented

    @abstractmethod
    def gate_received(self, gate, ship: Ship) -> Optional[bytes]:
        """
        Callback when new package received

        :param gate:       remote gate
        :param ship:       data package container
        :return response
        """
        raise NotImplemented


class Gate(ABC):
    """ Star Gate of remote peer """

    @property
    def delegate(self) -> GateDelegate:
        """ Get callback for receiving data """
        yield None

    @property
    def opened(self) -> bool:
        """ Check whether StarGate is not closed and the current Connection is active """
        raise NotImplemented

    @property
    def expired(self) -> bool:
        """ Check whether Connection Status is expired for maintaining """
        raise NotImplemented

    @property
    def status(self) -> GateStatus:
        """ Get status """
        raise NotImplemented

    @abstractmethod
    def send_payload(self, payload: bytes, priority: int = 0, delegate: Optional[ShipDelegate] = None) -> bool:
        """
        Send payload to remote peer

        :param payload:  request data
        :param priority: smaller is the faster, -1 means send it synchronously
        :param delegate: completion handler
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def send_ship(self, ship: StarShip) -> bool:
        """
        Send ship carrying payload

        :param ship: outgo ship
        :return False on error
        """
        raise NotImplemented

    #
    #   Connection
    #

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """
        Send data package

        :param data: package
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def receive(self, length: int, remove: bool) -> Optional[bytes]:
        """
        Get received data from cache

        :param length: how many bytes to receive
        :param remove: whether remove from cache
        :return: received data
        """
        raise NotImplemented

    #
    #   Ship Docking
    #

    @abstractmethod
    def park_ship(self, ship: StarShip) -> bool:
        """ Park this outgo Ship in a waiting queue for departure """
        raise NotImplemented

    @abstractmethod
    def pull_ship(self, sn: Optional[bytes] = None) -> Optional[StarShip]:
        """ Get a parking Ship (remove it from the waiting queue) """
        raise NotImplemented

    @abstractmethod
    def any_ship(self) -> Optional[StarShip]:
        """ Get any Ship timeout/expired (keep it in the waiting queue) """
        raise NotImplemented
