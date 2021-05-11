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

import weakref
from abc import ABC
from typing import Optional

from .runner import Runner

from .ship import ShipDelegate
from .starship import StarShip
from .dock import Dock, LockedDock
from .docker import Docker
from .gate import Gate, GateStatus, GateDelegate


class StarGate(Runner, Gate, ABC):
    """
        Star Gate
        ~~~~~~~~~

        @abstract properties:
            expired()
            status()

        @abstract methods:
            - _create_docker()
            - send(data)
            - receive(length, remove)
    """

    def __init__(self):
        super().__init__()
        self.__dock = self._create_dock()
        self.__docker: Optional[Docker] = None
        self.__delegate: Optional[weakref.ReferenceType] = None

    # noinspection PyMethodMayBeStatic
    def _create_dock(self) -> Dock:
        return LockedDock()

    @property
    def docker(self) -> Optional[Docker]:
        if self.__docker is None:
            self.__docker = self._create_docker()
        return self.__docker

    def _create_docker(self) -> Optional[Docker]:
        """ Override to customize Docker """
        raise NotImplemented

    @docker.setter
    def docker(self, worker: Docker):
        self.__docker = worker

    # Override
    @property
    def delegate(self) -> Optional[GateDelegate]:
        if self.__delegate is None:
            return None
        else:
            return self.__delegate()

    @delegate.setter
    def delegate(self, handler: GateDelegate):
        if handler is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(handler)

    @property
    def opened(self) -> bool:
        return self.running

    # Override
    def send_payload(self, payload: bytes, priority: int = 0, delegate: Optional[ShipDelegate] = None) -> bool:
        worker = self.docker
        if worker is not None:
            outgo = worker.pack(payload=payload, priority=priority, delegate=delegate)
            return self.send_ship(ship=outgo)

    # Override
    def send_ship(self, ship: StarShip) -> bool:
        if ship.priority <= StarShip.URGENT and self.status == GateStatus.Connected:
            # send out directly
            return self.send(data=ship.package)
        else:
            # put the Ship into a waiting queue
            return self.park_ship(ship=ship)

    #
    #   Docking
    #

    # Override
    def park_ship(self, ship: StarShip) -> bool:
        return self.__dock.put(ship=ship)

    # Override
    def pull_ship(self, sn: Optional[bytes] = None) -> Optional[StarShip]:
        return self.__dock.pop(sn=sn)

    # Override
    def any_ship(self) -> Optional[StarShip]:
        return self.__dock.any()

    #
    #   Runner
    #

    # Override
    def setup(self):
        super().setup()
        # check connection
        if not self.opened:
            # waiting for connection
            self._idle()
        # check docker
        while self.docker is None and self.opened:
            # waiting for docker
            self._idle()
        # setup docker
        if self.__docker is not None:
            self.__docker.setup()

    def finish(self):
        # clean docker
        if self.__docker is not None:
            self.__docker.finish()
        super().finish()

    def process(self) -> bool:
        if self.__docker is not None:
            return self.__docker.process()
        # else:
        #     raise AssertionError('Star worker not found!')
