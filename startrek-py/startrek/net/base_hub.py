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
from abc import ABC, abstractmethod
from typing import Optional, Dict

from ..types import AddressPairMap

from .connection import Connection
from .delegate import Delegate as ConnectionDelegate
from .hub import Hub


class BaseHub(Hub, ABC):

    DYING_EXPIRES = 120  # kill connection after 2 minutes

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)
        self.__connection_pool = AddressPairMap()
        self.__dying_times: Dict[tuple, int] = {}  # (remote, local) => timestamp

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    # Override
    def send_data(self, data: bytes, source: Optional[tuple], destination: tuple) -> bool:
        conn = self.__connection_pool.get(remote=destination, local=source)
        if conn is None:
            # connection lost
            return False
        # assert isinstance(conn, Connection), 'connection error: %s' % conn
        if not conn.alive:
            # connection not ready
            return False
        return conn.send(data=data, target=destination) != -1

    # Override
    def get_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Connection]:
        return self.__connection_pool.get(remote=remote, local=local)

    # Override
    def connect(self, remote: Optional[tuple], local: Optional[tuple]) -> Optional[Connection]:
        conn = self.__connection_pool.get(remote=remote, local=local)
        if conn is None:
            conn = self.create_connection(remote=remote, local=local)
            if conn is not None:
                self.__connection_pool.put(remote=remote, local=local, value=conn)
        return conn

    @abstractmethod
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        """
        Create connection with direction (remote, local)

        :param remote: remote address
        :param local:  local address
        :return new connection
        """
        raise NotImplemented

    # Override
    def disconnect(self, remote: Optional[tuple], local: Optional[tuple]):
        conn = self.__connection_pool.remove(remote=remote, local=local, value=None)
        if isinstance(conn, Connection):
            conn.close()

    # Override
    def process(self) -> bool:
        activated_count = 0
        connections = self.__connection_pool.values
        now = int(time.time())
        for conn in connections:
            assert isinstance(conn, Connection), 'connection error: %s' % conn
            # 1. drive all connections to process
            if conn.process():
                activated_count += 1
            remote = conn.remote_address
            local = conn.local_address
            pair = build_pair(remote=remote, local=local)
            # 2. check closed connections
            if conn.opened:
                # connection still alive, revive it
                self.__dying_times.pop(pair, None)
            else:
                # connection is closed, check dying time
                expired = self.__dying_times.get(pair)
                if expired is None or expired == 0:
                    # set death clock
                    self.__dying_times[pair] = now + self.DYING_EXPIRES
                elif expired < now:
                    # times up, kill it
                    self.__connection_pool.remove(remote=remote, local=local, value=conn)
                    # clear the death clock for it
                    self.__dying_times.pop(pair, None)
        return activated_count > 0


def build_pair(remote: Optional[tuple], local: Optional[tuple]) -> Optional[tuple]:
    if remote is None:
        if local is None:
            # raise ValueError('both local & remote addresses are empty')
            return None
        return ANY_REMOTE_ADDRESS, local
    elif local is None:
        return remote, ANY_LOCAL_ADDRESS
    else:
        return remote, local


ANY_LOCAL_ADDRESS = ('0.0.0.0', 0)
ANY_REMOTE_ADDRESS = ('0.0.0.0', 0)
