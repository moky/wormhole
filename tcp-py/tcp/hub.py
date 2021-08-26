# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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
from abc import ABC, abstractmethod
from typing import Optional

from .net import Channel
from .net import Connection, ConnectionDelegate
from .net import BaseConnection, ActiveConnection
from .net import BaseHub


class StreamHub(BaseHub):
    """ Base Stream Hub """

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
        conn = BaseConnection(remote=remote, local=local, channel=sock)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn

    @abstractmethod
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        raise NotImplemented


class ActiveStreamHub(StreamHub, ABC):
    """ Active Stream Hub """

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with addresses
        conn = ActiveStreamConnection(remote=remote, local=local, hub=self)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn


class ActiveStreamConnection(ActiveConnection):
    """ Active Stream Connection """

    def __init__(self, remote: tuple, local: Optional[tuple], hub: ActiveStreamHub):
        super().__init__(remote=remote, local=local)
        self.__hub = weakref.ref(hub)

    # Override
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        hub = self.__hub()
        # assert isinstance(hub, ActiveStreamHub)
        return hub.create_channel(remote=remote, local=local)
