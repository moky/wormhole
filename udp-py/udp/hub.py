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

import socket
import weakref
from abc import ABC
from typing import Optional, Dict

from startrek import Channel, Connection, ConnectionDelegate
from startrek import BaseHub, BaseConnection, ActiveConnection

from .channel import PackageChannel


class PackageHub(BaseHub, ABC):
    """ Base Package Hub """

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__channels: Dict[tuple, socket.socket] = {}  # address => socket

    def bind(self, address: Optional[tuple] = None, host: Optional[str] = None, port: Optional[int] = 0):
        if address is None:
            address = (host, port)
        sock = self.__channels.get(address)
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setblocking(True)
            sock.bind(address)
            sock.setblocking(False)
            self.__channels[address] = sock
        return self.connect(remote=None, local=address)

    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__channels.get(local)
        if sock is not None:
            return PackageChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class ServerHub(PackageHub):
    """ Package Server Hub """

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


class ClientHub(PackageHub):
    """ Package Client Hub """

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with addresses
        conn = ActivePackageConnection(remote=remote, local=local, hub=self)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn


class ActivePackageConnection(ActiveConnection):
    """ Active Package Connection """

    def __init__(self, remote: tuple, local: Optional[tuple], hub: PackageHub):
        super().__init__(remote=remote, local=local)
        self.__hub = weakref.ref(hub)

    @property
    def hub(self) -> PackageHub:
        return self.__hub()

    # Override
    def connect(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        return self.hub.create_channel(remote=remote, local=local)
