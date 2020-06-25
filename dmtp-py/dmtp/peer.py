# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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
from typing import Optional
from weakref import WeakValueDictionary

from udp import HubListener
from udp import Connection, ConnectionStatus
from udp.mtp import Peer as UDPPeer
from udp.mtp import Arrival


class Peer(UDPPeer, HubListener):

    def __init__(self):
        super().__init__()
        self.__connections = {}
        self.__connections_lock = threading.Lock()

    def is_connected(self, remote_address: tuple, local_address: tuple) -> bool:
        status = self.connection_status(remote_address=remote_address, local_address=local_address)
        return status == ConnectionStatus.Connected

    def connection_status(self, remote_address: tuple, local_address: tuple) -> ConnectionStatus:
        conn = self.get_connection(remote_address=remote_address, local_address=local_address)
        if conn is None:
            return ConnectionStatus.Error
        return conn.status

    def get_connection(self, remote_address: tuple, local_address: tuple) -> Optional[Connection]:
        with self.__connections_lock:
            table = self.__connections.get(local_address)
            if table is not None:
                return table.get(remote_address)

    def set_connection(self, connection: Connection):
        with self.__connections_lock:
            table = self.__connections.get(connection.local_address)
            if table is None:
                table = WeakValueDictionary()
                self.__connections[connection.local_address] = table
            table[connection.remote_address] = connection

    def remove_connection(self, connection: Connection) -> bool:
        with self.__connections_lock:
            table = self.__connections.get(connection.local_address)
            if table is not None:
                assert isinstance(table, WeakValueDictionary), 'connection table error: %s' % table
                return table.pop(connection.remote_address, None) is not None

    #
    #   HubListener
    #
    def data_received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        task = Arrival(payload=data, source=source, destination=destination)
        self.pool.append_arrival(task=task)
        return None

    def status_changed(self, connection: Connection, old_status: ConnectionStatus, new_status: ConnectionStatus):
        if new_status == ConnectionStatus.Connected:
            self.set_connection(connection=connection)
        else:
            self.remove_connection(connection=connection)
