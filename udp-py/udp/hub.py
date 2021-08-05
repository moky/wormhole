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

from .net import PackageConnection, ActivePackageConnection
from .net import BasePackageHub


class PackageHub(BasePackageHub):
    """ Base Package Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    def create_connection(self, remote: tuple, local: Optional[tuple] = None) -> Connection:
        sock = self.create_channel(remote=remote, local=local)
        conn = PackageConnection(channel=sock)
        if conn.delegate is None:
            conn.delegate = self.delegate
        conn.start()  # start FSM
        return conn

    @abstractmethod
    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        raise NotImplemented


class ActivePackageHub(PackageHub, ABC):
    """ Active Package Hub """

    def create_connection(self, remote: tuple, local: Optional[tuple] = None) -> Connection:
        conn = ActiveDiscreteConnection(remote=remote, local=local, hub=self)
        if conn.delegate is None:
            conn.delegate = self.delegate
        conn.start()  # start FSM
        return conn


class ActiveDiscreteConnection(ActivePackageConnection):
    """ Active Discrete Package Connection """

    def __init__(self, remote: tuple, local: tuple, hub: ActivePackageHub):
        super().__init__(remote=remote, local=local)
        self.__hub = weakref.ref(hub)

    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        hub = self.__hub()
        # assert isinstance(hub, ActiveStreamHub)
        return hub.create_channel(remote=remote, local=local)
