# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
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

import time
from abc import ABC, abstractmethod
from enum import IntEnum


class ConnectionStatus(IntEnum):

    Error = -1
    Default = 0
    Connecting = 1
    Connected = 2


def connection_status(now: float, send_expired: float, receive_expired: float, connection_lost: float):
    if now < receive_expired:
        """
        When received a package from remote address, this node must respond
        a package, so 'send expired' is always late than 'receive expired'.
        So, if received anything (normal package or just 'PING') from this
        connection, this indicates 'Connected'.
        """
        return ConnectionStatus.Connected
    elif now > connection_lost:
        """
        It's a long time to receive nothing (even a 'PONG'), this connection
        may be already lost, needs to reconnect again.
        """
        return ConnectionStatus.Error
    elif now < send_expired:
        """
        If sent package through this connection recently but not received
        anything yet (includes 'PONG'), this indicates 'Connecting'.
        """
        return ConnectionStatus.Connecting
    else:
        """
        It's a long time to send nothing, this connection needs maintaining,
        send something immediately (e.g.: 'PING') to keep it alive.
        """
        return ConnectionStatus.Default


class Connection:

    EXPIRES = 28  # seconds

    def __init__(self, local_address: tuple, remote_address: tuple):
        super().__init__()
        self.__local_address = local_address
        self.__remote_address = remote_address
        # connecting time
        now = time.time()
        self.__connection_lost = now + (self.EXPIRES << 4)
        self.__receive_expired = now  # + self.EXPIRES
        self.__send_expired = now  # + self.EXPIRES

    @property
    def local_address(self) -> tuple:
        """ local ip, port """
        return self.__local_address

    @property
    def remote_address(self) -> tuple:
        """ remote ip, port """
        return self.__remote_address

    @property
    def status(self) -> ConnectionStatus:
        return connection_status(now=time.time(),
                                 send_expired=self.__send_expired,
                                 receive_expired=self.__receive_expired,
                                 connection_lost=self.__connection_lost)

    def update_sent_time(self) -> (ConnectionStatus, ConnectionStatus):
        now = time.time()
        # old status
        o_cs = connection_status(now,
                                 send_expired=self.__send_expired,
                                 receive_expired=self.__receive_expired,
                                 connection_lost=self.__connection_lost)
        # update last send time
        self.__send_expired = now + self.EXPIRES
        # new status
        n_cs = connection_status(now,
                                 send_expired=self.__send_expired,
                                 receive_expired=self.__receive_expired,
                                 connection_lost=self.__connection_lost)
        return o_cs, n_cs

    def update_received_time(self) -> (ConnectionStatus, ConnectionStatus):
        now = time.time()
        # old status
        o_cs = connection_status(now,
                                 send_expired=self.__send_expired,
                                 receive_expired=self.__receive_expired,
                                 connection_lost=self.__connection_lost)
        # update last receive time
        self.__connection_lost = now + (self.EXPIRES << 4)
        self.__receive_expired = now + self.EXPIRES
        # new status
        n_cs = connection_status(now,
                                 send_expired=self.__send_expired,
                                 receive_expired=self.__receive_expired,
                                 connection_lost=self.__connection_lost)
        return o_cs, n_cs


class ConnectionDelegate(ABC):

    @abstractmethod
    def connection_status_changed(self, connection: Connection,
                                  old_status: ConnectionStatus, new_status: ConnectionStatus):
        """
        Call when connection status changed

        :param connection:
        :param old_status:
        :param new_status:
        """
        pass

    @abstractmethod
    def connection_received_data(self, connection: Connection):
        """
        Call when received data from a connection

        :param connection:
        """
        pass
