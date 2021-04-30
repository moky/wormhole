# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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

from abc import ABC, abstractmethod

from .status import ConnectionStatus


class ConnectionDelegate(ABC):

    # @abstractmethod
    def connection_changed(self, connection, old_status: ConnectionStatus, new_status: ConnectionStatus):
        """
        Call when connection status changed

        :param connection: current connection
        :param old_status: status before
        :param new_status: status after
        """
        pass

    @abstractmethod
    def connection_received(self, connection, data: bytes):
        """
        Call when received data from a connection
        (if data processed, must call 'connection.receive(length=len(data))' to remove it from cache pool)

        :param connection: current connection
        :param data:       received data
        """
        pass

    # @abstractmethod
    def connection_overflowed(self, connection, ejected: bytes):
        """
        Call when connection's cache is full

        :param connection: current connection
        :param ejected:    dropped data
        :return:
        """
        pass
