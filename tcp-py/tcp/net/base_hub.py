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

import threading
import time
import weakref
from abc import abstractmethod
from typing import Optional, Set, Dict, MutableMapping

from ..fsm import Ticker

from .connection import Connection
from .hub import Hub


class BaseHub(Hub, Ticker):

    """
        Maximum Segment Size
        ~~~~~~~~~~~~~~~~~~~~
        Buffer size for receiving package

        MTU        : 1500 bytes (excludes 14 bytes ethernet header & 4 bytes FCS)
        IP header  :   20 bytes
        TCP header :   20 bytes
        UDP header :    8 bytes
    """
    MSS = 1472  # 1500 - 20 - 8

    DYING_EXPIRES = 120  # kill connection after 2 minutes

    def __init__(self):
        super().__init__()
        self.__lock = threading.RLock()
        self.__connections: Set[Connection] = set()
        # because the remote address will always different to local address, so
        # we shared the same map for all directions here:
        #    mapping: (remote, local) => Connection
        #    mapping: (remote, null) => Connection
        #    mapping: (local, null) => Connection
        self.__map: Dict[tuple, MutableMapping[tuple, Connection]] = {}
        # mapping: (remote, local) => time to kill
        self.__dying_times: Dict[tuple, int] = {}

    @abstractmethod
    def create_connection(self, remote: tuple, local: tuple) -> Connection:
        raise NotImplemented

    def __seek(self, remote: tuple, local: tuple) -> Optional[Connection]:
        if remote is None:
            assert local is not None, 'both local & remote addresses are empty'
            # get connection bound to local address
            table = self.__map.get(local)
            if table is None:
                return None
            else:
                # mapping: (local, null) => Connection
                conn = table.get(ANY_REMOTE_ADDRESS)
                if conn is not None:
                    return conn
            # get any connection bound to this local address
            for _, v in table:
                if v is not None:
                    return v
        else:
            # get connections connected to remote address
            table = self.__map.get(remote)
            if table is None:
                return None
            elif local is not None:
                # mapping: (remote, local) => Connection
                return table.get(local)
            else:
                # mapping: (remote, null) => Connection
                conn = table.get(ANY_LOCAL_ADDRESS)
                if conn is not None:
                    return conn
            # get any connection connected to this remote address
            for _, v in table:
                if v is not None:
                    return v

    def __create_indexes(self, connection: Connection, remote: tuple, local: tuple) -> bool:
        if remote is None:
            if local is None:
                # raise ValueError('both local & remote addresses are empty')
                return False
            # get table for local address
            table = self.__map.get(local)
            if table is None:
                table = weakref.WeakValueDictionary()
                self.__map[local] = table
            # mapping: (local, null) => Connection
            table[ANY_REMOTE_ADDRESS] = connection
        else:
            # get table for remote address
            table = self.__map.get(remote)
            if table is None:
                table = weakref.WeakValueDictionary()
                self.__map[remote] = table
            if local is None:
                # mapping: (remote, null) => Connection
                table[ANY_LOCAL_ADDRESS] = connection
            else:
                # mapping: (remote, local) => Connection
                table[local] = connection
        return True

    def __remove_indexes(self, connection: Connection):
        remote = connection.remote_address
        local = connection.local_address
        if remote is None:
            if local is None:
                # raise ValueError('both local & remote addresses are empty')
                return
            # get table for local address
            table = self.__map.get(local)
            if table is not None:
                # mapping: (local, null) => Connection
                table.pop(ANY_REMOTE_ADDRESS, None)
        else:
            # get table for remote address
            table = self.__map.get(remote)
            if table is not None:
                if local is None:
                    # mapping: (remote, null) => Connection
                    table.pop(ANY_LOCAL_ADDRESS, None)
                else:
                    # mapping: (remote, local) => Connection
                    table.pop(local, None)

    def __remove(self, connection: Connection):
        with self.__lock:
            self.__remove_indexes(connection=connection)
            self.__connections.remove(connection)

    #
    #   Hub
    #

    def send(self, data: bytes, source: Optional[tuple], destination: tuple) -> bool:
        conn = self.connect(remote=destination, local=source)
        if conn is None or not conn.opened:
            # connection closed
            return False
        return conn.send(data=data, target=destination) != -1

    def receive(self, source: Optional[tuple], destination: Optional[tuple]) -> Optional[bytes]:
        conn = self.connect(remote=source, local=destination)
        if conn is None or not conn.opened:
            # connection closed
            return None
        return conn.receive(max_len=self.MSS)

    def get_connection(self, remote: tuple, local: tuple) -> Optional[Connection]:
        with self.__lock:
            return self.__seek(remote=remote, local=local)

    def connect(self, remote: tuple, local: tuple) -> Optional[Connection]:
        # 1. try to get connection from cache pool
        conn = self.get_connection(remote=remote, local=local)
        if conn is not None:
            return conn
        # 2. connection not found, try to create connection
        with self.__lock:
            # double check to make sure the connection doesn't exist
            conn = self.__seek(remote=remote, local=local)
            if conn is None:
                # create it
                conn = self.create_connection(remote=remote, local=local)
                if conn is not None and self.__create_indexes(connection=conn, remote=remote, local=local):
                    # make sure different connection with same pair(remote, local) not exists
                    self.__connections.remove(conn)
                    # cache it
                    self.__connections.add(conn)

    def disconnect(self, remote: tuple, local: tuple):
        with self.__lock:
            conn = self.__seek(remote=remote, local=local)
        if conn is not None:
            self.__remove(connection=conn)
            conn.close()

    #
    #   Ticker
    #

    def tick(self):
        # call 'tick()' to drive all connections
        candidates = set()
        with self.__lock:
            for conn in self.__connections:
                conn.tick()
                candidates.add(conn)
        # check closed connection(s)
        now = int(time.time())
        for conn in candidates:
            remote = conn.remote_address
            local = conn.local_address
            if remote is None and local is None:
                # should not happen
                self.__remove(connection=conn)
                continue
            pair = (remote, local)
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
                    self.__remove(connection=conn)
                    # clear the death clock for it
                    self.__dying_times.pop(pair, None)


ANY_LOCAL_ADDRESS = ('0.0.0.0', 0)
ANY_REMOTE_ADDRESS = ('0.0.0.0', 0)