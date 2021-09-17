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

from abc import abstractmethod
from typing import Optional

from ..fsm import Processor

from .ship import Departure, ShipDelegate


class Docker(Processor):
    """
        Star Worker
        ~~~~~~~~~~~

        Processor for Star Ships
    """

    @property
    def remote_address(self) -> tuple:
        """ Remote address of connection """
        raise NotImplemented

    @property
    def local_address(self) -> Optional[tuple]:
        """ Local address of connection """
        raise NotImplemented

    @abstractmethod
    def pack(self, payload: bytes, priority: int = 0, delegate: Optional[ShipDelegate] = None) -> Departure:
        """
        Pack the payload to an outgo Ship

        :param payload:  request data
        :param priority: smaller is faster (-1 is the most fast)
        :param delegate: callback handler for the departure ship
        :return: Departure ship carrying package with payload
        """
        raise NotImplemented

    @abstractmethod
    def append_departure(self, ship: Departure) -> bool:
        """
        Append outgo ship to a queue for sending out

        :param ship: outgo ship carrying data package/fragment
        :return: False on duplicated
        """
        raise NotImplemented

    @abstractmethod
    def process_received(self, data: bytes):
        """
        Called when received data

        :param data: received data package
        """
        raise NotImplemented

    @abstractmethod
    def heartbeat(self):
        """
        Send 'PING' for keeping connection alive
        """
        raise NotImplemented

    @abstractmethod
    def purge(self):
        """ Clear all expired tasks """
        raise NotImplemented
