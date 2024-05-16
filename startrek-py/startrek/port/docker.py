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
from enum import IntEnum
from typing import Optional, Union

from ..types import SocketAddress
from ..skywalker import Processor
from ..net import ConnectionState
from ..net.state import StateOrder

from .ship import Departure


class DockerStatus(IntEnum):
    """ Docker Status """
    ERROR = -1
    INIT = 0
    PREPARING = 1
    READY = 2


READY_STATUS = [
    StateOrder.READY,
    StateOrder.EXPIRED,
    StateOrder.MAINTAINING
]


def status_from_state(state: Optional[ConnectionState]) -> DockerStatus:
    """ Convert connection state to docker status """
    if state is None:
        return DockerStatus.ERROR
    index = state.index
    if index in READY_STATUS:
        return DockerStatus.READY
    if index == StateOrder.PREPARING:
        return DockerStatus.PREPARING
    if index == StateOrder.ERROR:
        return DockerStatus.ERROR
    return DockerStatus.INIT


class Docker(Processor):
    """
        Star Worker
        ~~~~~~~~~~~

        Processor for Star Ships
    """

    @property
    @abstractmethod
    def closed(self) -> bool:
        """ Connection closed """
        raise NotImplemented

    @property
    @abstractmethod
    def alive(self) -> bool:
        """ Connection alive """
        raise NotImplemented

    @property
    @abstractmethod
    def status(self) -> DockerStatus:
        """ Connection state """
        raise NotImplemented

    @property
    @abstractmethod
    def remote_address(self) -> SocketAddress:
        """ Remote address of connection """
        raise NotImplemented

    @property
    @abstractmethod
    def local_address(self) -> Optional[SocketAddress]:
        """ Local address of connection """
        raise NotImplemented

    @abstractmethod
    async def send_data(self, payload: Union[bytes, bytearray]) -> bool:
        """
        Pack data to an outgo ship (with normal priority), and
        append to the waiting queue for sending out

        :param payload: data to be sent
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    async def send_ship(self, ship: Departure) -> bool:
        """
        Append outgo ship (carrying data package, with priority)
        to the waiting queue for sending out

        :param ship: outgo ship carrying data package/fragment
        :return: False on duplicated
        """
        raise NotImplemented

    @abstractmethod
    async def process_received(self, data: bytes):
        """
        Called when received data

        :param data: received data package
        """
        raise NotImplemented

    @abstractmethod
    async def heartbeat(self):
        """
        Send 'PING' for keeping connection alive
        """
        raise NotImplemented

    @abstractmethod
    def purge(self, now: float) -> int:
        """ Clear all expired tasks """
        raise NotImplemented

    @abstractmethod
    async def close(self):
        """ Close connection for this docker """
        raise NotImplemented
