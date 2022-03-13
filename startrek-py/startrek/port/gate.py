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
from typing import Optional

from ..types import Address
from ..fsm import Processor

from .ship import Departure
from .docker import Docker


class Gate(Processor, ABC):
    """
        Star Gate
        ~~~~~~~~~
    """

    @abstractmethod
    def send_ship(self, ship: Departure, remote: Address, local: Optional[Address]) -> bool:
        """
        Send outgo ship (carrying data package) by docker

        :param ship:   departure ship
        :param remote: remote address
        :param local:  local address
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def get_docker(self, remote: Address, local: Optional[Address]) -> Optional[Docker]:
        """
        Get docker with direction

        :param remote: remote address
        :param local:  local address
        :return: None on failed
        """
        raise NotImplemented

    @abstractmethod
    def set_docker(self, remote: Address, local: Optional[Address], docker: Optional[Docker]):
        """
        Set docker with direction

        :param remote: remote address
        :param local:  local address
        :param docker: connection docker
        """
        raise NotImplemented
