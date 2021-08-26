# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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
from abc import ABC, abstractmethod
from typing import Optional

from tcp import Channel, Connection, ConnectionDelegate
from tcp import BaseHub

from .mtp import Package, Departure
from .net import PackageConnection, ActivePackageConnection


class PackageHub(BaseHub):
    """ Base Package Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with channel
        sock = self.create_channel(remote=remote, local=local)
        conn = PackageConnection(remote=remote, local=local, channel=sock)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn

    @abstractmethod
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        raise NotImplemented

    def send_command(self, body: bytes, source: Optional[tuple], destination: tuple) -> Departure:
        conn = self.connect(remote=destination, local=source)
        assert isinstance(conn, PackageConnection), 'connection error: %s' % conn
        return conn.send_command(body=body, source=source, destination=destination)

    def send_message(self, body: bytes, source: Optional[tuple], destination: tuple) -> Departure:
        conn = self.connect(remote=destination, local=source)
        assert isinstance(conn, PackageConnection), 'connection error: %s' % conn
        return conn.send_message(body=body, source=source, destination=destination)

    def send_package(self, pack: Package, source: Optional[tuple], destination: tuple) -> Departure:
        conn = self.connect(remote=destination, local=source)
        assert isinstance(conn, PackageConnection), 'connection error: %s' % conn
        return conn.send_package(pack=pack, source=source, destination=destination)


class ActivePackageHub(PackageHub, ABC):
    """ Active Package Hub """

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with addresses
        conn = ActiveDiscreteConnection(remote=remote, local=local, hub=self)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn


class ActiveDiscreteConnection(ActivePackageConnection):
    """ Active Discrete Package Connection """

    def __init__(self, remote: tuple, local: Optional[tuple], hub: ActivePackageHub):
        super().__init__(remote=remote, local=local)
        self.__hub = weakref.ref(hub)

    # Override
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        hub = self.__hub()
        # assert isinstance(hub, ActivePackageHub)
        return hub.create_channel(remote=remote, local=local)
