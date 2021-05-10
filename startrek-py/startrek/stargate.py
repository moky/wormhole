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

import time
import weakref
from typing import Optional

from tcp import Connection, ConnectionStatus, ConnectionDelegate

from .ship import ShipDelegate
from .starship import StarShip
from .dock import Dock, LockedDock
from .docker import Docker
from .gate import gate_status
from .gate import Gate, GateStatus, GateDelegate


class StarGate(Gate, ConnectionDelegate):

    def __init__(self, connection: Connection):
        super().__init__()
        self.__dock = self._create_dock()
        self.__conn = connection
        self.__chunks: Optional[bytes] = None
        self.__docker: Optional[Docker] = None
        self.__delegate: Optional[weakref.ReferenceType] = None
        self.__running = False

    # noinspection PyMethodMayBeStatic
    def _create_dock(self) -> Dock:
        return LockedDock()

    @property
    def connection(self) -> Connection:
        return self.__conn

    @property
    def docker(self) -> Optional[Docker]:
        if self.__docker is None:
            self.__docker = self._create_docker()
        return self.__docker

    def _create_docker(self) -> Optional[Docker]:
        # override to customize Docker
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
        if self.__running:
            # connection not closed or still have data unprocessed
            return self.__conn.alive or self.__conn.available > 0

    @property
    def expired(self) -> bool:
        return self.__conn.status == ConnectionStatus.Expired

    # Override
    @property
    def status(self) -> GateStatus:
        return gate_status(status=self.__conn.status)

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
    #   Connection
    #

    # Override
    def send(self, data: bytes) -> bool:
        if self.__conn.alive:
            return self.__conn.send(data=data) == len(data)

    # Override
    def receive(self, length: int, remove: bool) -> Optional[bytes]:
        fragment = self.__receive(length=length)
        if fragment is not None:
            if len(fragment) > length:
                if remove:
                    self.__chunks = fragment[length:]
                return fragment[:length]
            elif remove:
                # assert len(fragment) == length, 'fragment length error'
                self.__chunks = None
            return fragment

    def __receive(self, length: int) -> Optional[bytes]:
        cached = 0
        if self.__chunks is not None:
            cached = len(self.__chunks)
        while cached < length:
            # check available length from connection
            available = self.__conn.available
            if available <= 0:
                break
            # try to receive data from connection
            data = self.__conn.receive(max_length=available)
            if data is None:
                break
            # append data
            if self.__chunks is None:
                self.__chunks = data
            else:
                self.__chunks += data
            cached += len(data)
        return self.__chunks

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
    #   Running
    #

    def run(self):
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    def stop(self):
        self.__running = False

    def setup(self):
        self.__running = True
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
        self.__running = False
        # clean docker
        if self.__docker is not None:
            self.__docker.finish()

    # Override
    def handle(self):
        while self.opened:
            if not self.process():
                self._idle()

    # noinspection PyMethodMayBeStatic
    def _idle(self):
        time.sleep(0.1)

    def process(self) -> bool:
        if self.__docker is None:
            # raise AssertionError('Star worker not found!')
            return False
        else:
            return self.__docker.process()

    #
    #   ConnectionDelegate
    #

    # Override
    def connection_changed(self, connection, old_status: ConnectionStatus, new_status: ConnectionStatus):
        s1 = gate_status(status=old_status)
        s2 = gate_status(status=new_status)
        if s1 != s2:
            delegate = self.delegate
            if delegate is not None:
                delegate.gate_status_changed(gate=self, old_status=s1, new_status=s2)

    # Override
    def connection_received(self, connection, data: bytes):
        # received data will be processed in run loop (StarDocker::handle),
        # do nothing here
        pass
